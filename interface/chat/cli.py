"""
interface/chat/cli.py

CLI Chat Interface - Terminal tabanli UEM chat.
UEM v2 - Interaktif sohbet arayuzu.

Ozellikler:
- Interaktif chat loop
- Komut destegi (/help, /quit, /history, /recall, /stats, /debug, /clear)
- Debug modu
- Session yonetimi
- Pipeline modu (Faz 4) - /pipeline on/off/status, /pipeinfo
"""

import os
import sys
from typing import Optional, List, Any
import argparse
import logging

# UEM imports - graceful
try:
    from core.language import (
        UEMChatAgent,
        ChatConfig,
        ChatResponse,
        MockLLMAdapter,
    )
    from core.language.conversation import ContextManager
    UEM_AVAILABLE = True
except ImportError:
    UEM_AVAILABLE = False

# Faz 5 - Episode Logging
try:
    from core.learning import (
        EpisodeLogger,
        JSONLEpisodeStore,
        PatternAnalyzer,
    )
    from core.learning.episode_types import ImplicitFeedback
    EPISODE_LOGGING_AVAILABLE = True
except ImportError:
    EPISODE_LOGGING_AVAILABLE = False

# Implicit feedback detection patterns
THANK_PATTERNS = [
    "teşekkür", "tesekkur", "thanks", "thank you",
    "sağol", "sagol", "sağ ol", "sag ol",
    "eyvallah", "eyv", "saol", "çok iyi",
    "teşekkürler", "tesekkurler", "mersi"
]

logger = logging.getLogger(__name__)


class CLIChat:
    """
    CLI Chat Interface.

    Terminal tabanli interaktif UEM chat arayuzu.

    Kullanim:
        cli = CLIChat()
        cli.start()

    Komutlar:
        /help     - Komutlari goster
        /quit     - Cikis
        /exit     - Cikis
        /history  - Son 10 mesaji goster
        /recall   - Ani ara (semantic search)
        /stats    - Session istatistikleri
        /debug    - Debug modunu ac/kapat
        /clear    - Ekrani temizle
        /good, /+ - Pozitif feedback
        /bad, /-  - Negatif feedback
        /learned  - Ogrenilen pattern sayisi
        /analyze  - Episode pattern analizi
        /pipeline - Pipeline modu (on/off/status)
        /pipeinfo - Son pipeline isleminin detaylari
    """

    def __init__(
        self,
        agent: Optional[Any] = None,
        user_id: str = "cli_user",
        show_debug: bool = False,
    ):
        """
        Initialize CLI Chat.

        Args:
            agent: UEMChatAgent instance (opsiyonel)
            user_id: Kullanici ID
            show_debug: Debug modu
        """
        if agent is not None:
            self.agent = agent
        elif UEM_AVAILABLE:
            self.agent = UEMChatAgent()
        else:
            raise ImportError("UEMChatAgent not available")

        self.user_id = user_id
        self.show_debug = show_debug
        self._running = False
        self._session_id: Optional[str] = None

        # Context Manager (Faz 5)
        self._context_manager: Optional[ContextManager] = None
        if UEM_AVAILABLE:
            self._context_manager = ContextManager()
            logger.info("ContextManager initialized for episode logging")

        # Faz 5 - Episode Logging
        self._episode_store: Optional[Any] = None
        self._episode_logger: Optional[Any] = None
        if EPISODE_LOGGING_AVAILABLE:
            self._episode_store = JSONLEpisodeStore("data/episodes.jsonl")
            logger.info("Episode logging enabled (data/episodes.jsonl)")

        # Implicit feedback tracking
        self._last_episode_id: Optional[str] = None
        self._last_user_intent: Optional[str] = None
        self._second_last_user_intent: Optional[str] = None

        logger.info(f"CLIChat initialized (user={user_id}, debug={show_debug})")

    # ===================================================================
    # MAIN LOOP
    # ===================================================================

    def start(self) -> None:
        """
        Start chat loop.

        Ana interaktif chat dongusunu baslatir.
        Ctrl+C veya /quit ile cikilir.
        """
        self._running = True
        self._print_welcome()
        self._session_id = self.agent.start_session(self.user_id)

        # Faz 5 - Initialize episode logger with session ID
        if EPISODE_LOGGING_AVAILABLE and self._episode_store:
            self._episode_logger = EpisodeLogger(self._episode_store, self._session_id)
            # Inject into agent's pipeline if available
            if hasattr(self.agent, '_pipeline') and self.agent._pipeline:
                self.agent._pipeline.episode_logger = self._episode_logger
                logger.info(f"Episode logger injected into pipeline (session={self._session_id})")

        # Inject ContextManager into pipeline
        if self._context_manager and hasattr(self.agent, '_pipeline') and self.agent._pipeline:
            self.agent._pipeline.context_manager = self._context_manager
            logger.info("ContextManager injected into pipeline")

        while self._running:
            user_input = self._get_input()

            if user_input is None:
                continue

            if not user_input:
                continue

            if self._is_command(user_input):
                self._handle_command(user_input)
            else:
                self._handle_message(user_input)

        self._print_goodbye()

    def stop(self) -> None:
        """
        Stop chat loop.

        Chat dongusunu durdurur ve session'i kapatir.
        Also marks conversation_continued for the last episode.
        """
        # Mark conversation_continued for last episode (session ended normally)
        self._mark_conversation_continued()

        self._running = False
        if self.agent:
            self.agent.end_session(self.user_id)
        logger.info("CLIChat stopped")

    # ===================================================================
    # INPUT / OUTPUT
    # ===================================================================

    def _get_input(self) -> Optional[str]:
        """
        Get user input from terminal.

        Handles encoding errors gracefully (replaces invalid UTF-8).

        Returns:
            User input string or None if interrupted
        """
        try:
            user_input = input("\nSen: ").strip()
            # Clean surrogate characters that cause JSON encoding errors
            if user_input:
                # Encode with 'replace' to remove surrogates, then decode
                user_input = user_input.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            return user_input
        except (KeyboardInterrupt, EOFError):
            print()  # New line after Ctrl+C
            self.stop()
            return None

    def _print_response(self, response: ChatResponse) -> None:
        """
        Print agent response.

        Args:
            response: ChatResponse from agent
        """
        print(f"\nUEM: {response.content}")

        if self.show_debug:
            self._print_debug_info(response)

    def _print_debug_info(self, response: ChatResponse) -> None:
        """
        Print debug information.

        Args:
            response: ChatResponse with debug info
        """
        debug_parts = []

        # Show source (llm or learned)
        source = getattr(response, 'source', 'llm')
        debug_parts.append(f"Source={source}")

        if response.emotion:
            valence = getattr(response.emotion, 'pleasure', 0) or getattr(response.emotion, 'valence', 0)
            arousal = getattr(response.emotion, 'arousal', 0.5)
            debug_parts.append(f"V={valence:.2f}, A={arousal:.2f}")

        if response.intent:
            debug_parts.append(f"Intent={response.intent}")

        if response.llm_response and response.llm_response.latency_ms:
            debug_parts.append(f"Latency={response.llm_response.latency_ms:.0f}ms")

        if debug_parts:
            print(f"   [Debug: {', '.join(debug_parts)}]")

    def _print_welcome(self) -> None:
        """Print welcome message."""
        print("\n" + "=" * 50)
        print("      UEM Chat - Unified Emotional Mind")
        print("=" * 50)
        print("\nMerhaba! Ben UEM, size nasil yardimci olabilirim?")
        print("Komutlar icin /help yazin. Cikmak icin /quit.\n")

    def _print_goodbye(self) -> None:
        """Print goodbye message."""
        print("\n" + "-" * 50)
        print("Gorusuruz! Iyi gunler.")
        print("-" * 50 + "\n")

    # ===================================================================
    # COMMAND HANDLING
    # ===================================================================

    def _is_command(self, text: str) -> bool:
        """
        Check if text is a command.

        Args:
            text: User input

        Returns:
            True if starts with /
        """
        return text.startswith("/")

    def _handle_command(self, command: str) -> None:
        """
        Handle slash command.

        Args:
            command: Command string (e.g., "/help")
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd in ["/help", "/h", "/?"]:
            self._cmd_help()
        elif cmd in ["/quit", "/q", "/exit"]:
            self._cmd_quit()
        elif cmd in ["/history", "/hist"]:
            self._cmd_history()
        elif cmd in ["/recall", "/r", "/search"]:
            self._cmd_recall(args)
        elif cmd in ["/stats", "/s"]:
            self._cmd_stats()
        elif cmd in ["/debug", "/d"]:
            self._cmd_debug()
        elif cmd in ["/clear", "/cls"]:
            self._cmd_clear()
        elif cmd in ["/good", "/+", "/like"]:
            self._cmd_good(args)
        elif cmd in ["/bad", "/-", "/dislike"]:
            self._cmd_bad(args)
        elif cmd in ["/learned", "/patterns"]:
            self._cmd_learned()
        elif cmd in ["/analyze", "/analysis", "/report"]:
            self._cmd_analyze()
        elif cmd in ["/pipeline", "/pipe", "/p"]:
            self._cmd_pipeline(args)
        elif cmd in ["/pipeinfo", "/pi", "/pdebug"]:
            self._cmd_pipeinfo()
        else:
            self._cmd_unknown(cmd)

    def _cmd_help(self) -> None:
        """Show help message."""
        print("\n--- Komutlar ---")
        print("/help, /h     - Bu mesaji goster")
        print("/quit, /exit  - Cikis yap")
        print("/history      - Son 10 mesaji goster")
        print("/recall <q>   - Ani ara (semantic search)")
        print("/stats        - Session istatistikleri")
        print("/debug        - Debug modunu ac/kapat")
        print("/clear        - Ekrani temizle")
        print("/good, /+     - Pozitif feedback (son cevap icin)")
        print("/bad, /-      - Negatif feedback (son cevap icin)")
        print("/learned      - Ogrenilen pattern sayisi")
        print("/analyze      - Episode pattern analizi")
        print("")
        print("--- Pipeline (Faz 4) ---")
        print("/pipeline on  - Pipeline modunu ac")
        print("/pipeline off - Pipeline modunu kapat (LLM kullan)")
        print("/pipeline     - Mevcut pipeline durumu")
        print("/pipeinfo     - Son islemin detaylari")
        print("------------------------")

    def _cmd_quit(self) -> None:
        """Quit chat."""
        self.stop()

    def _cmd_history(self) -> None:
        """Show conversation history."""
        history = self.agent.get_conversation_history(n=10)

        if not history:
            print("\n[Gecmis bos]")
            return

        print("\n--- Son Mesajlar ---")
        for turn in history:
            if hasattr(turn, 'role'):
                role = turn.role
                content = turn.content if hasattr(turn, 'content') else str(turn)
            elif isinstance(turn, dict):
                role = turn.get('role', 'unknown')
                content = turn.get('content', '')
            else:
                role = 'unknown'
                content = str(turn)

            role_label = "Sen" if role == "user" else "UEM"
            # Truncate long messages
            if len(content) > 100:
                content = content[:97] + "..."
            print(f"  {role_label}: {content}")
        print("--------------------")

    def _cmd_recall(self, query: str) -> None:
        """
        Search memories.

        Args:
            query: Search query
        """
        if not query:
            print("\n[Kullanim: /recall <arama sorgusu>]")
            return

        memories = self.agent.recall(query, k=5)

        if not memories:
            print(f"\n['{query}' icin ani bulunamadi]")
            return

        print(f"\n--- '{query}' icin Anilar ---")
        for i, mem in enumerate(memories, 1):
            if hasattr(mem, 'content'):
                content = mem.content
                sim = getattr(mem, 'similarity', 0)
            elif isinstance(mem, dict):
                content = mem.get('content', '')
                sim = mem.get('similarity', 0)
            else:
                content = str(mem)
                sim = 0

            # Truncate
            if len(content) > 80:
                content = content[:77] + "..."
            print(f"  {i}. ({sim:.2f}) {content}")
        print("-----------------------------")

    def _cmd_stats(self) -> None:
        """Show session statistics."""
        stats = self.agent.get_session_stats()

        print("\n--- Session Istatistikleri ---")
        print(f"  Session ID: {stats.get('session_id', 'N/A')}")
        print(f"  Kullanici: {stats.get('user_id', 'N/A')}")
        print(f"  Turn sayisi: {stats.get('turn_count', 0)}")
        print(f"  Toplam session: {stats.get('total_sessions', 0)}")
        print(f"  Toplam turn: {stats.get('total_turns', 0)}")

        avg_emotion = stats.get('average_emotion')
        if avg_emotion:
            print(f"  Ort. Duygu: P={avg_emotion.get('pleasure', 0):.2f}")

        # Learning stats
        patterns = stats.get('patterns_learned', 0)
        learned_responses = stats.get('learned_responses', 0)
        print(f"  Ogrenilen pattern: {patterns}")
        print(f"  Ogrenilmis cevap: {learned_responses}")

        print("------------------------------")

    def _cmd_debug(self) -> None:
        """Toggle debug mode."""
        self.show_debug = not self.show_debug
        status = "ACIK" if self.show_debug else "KAPALI"
        print(f"\n[Debug modu: {status}]")

    def _cmd_clear(self) -> None:
        """Clear screen."""
        # Cross-platform clear
        os.system('cls' if os.name == 'nt' else 'clear')
        self._print_welcome()

    def _cmd_unknown(self, cmd: str) -> None:
        """Handle unknown command."""
        print(f"\n[Bilinmeyen komut: {cmd}]")
        print("[Komutlar icin /help yazin]")

    def _cmd_good(self, reason: str = "") -> None:
        """
        Give positive feedback for last response.

        Args:
            reason: Optional reason for feedback
        """
        success = False

        # Episode logging feedback (JSONL update)
        if self._episode_logger:
            episode_success = self._episode_logger.add_feedback_to_last(explicit=1.0)
            if episode_success:
                success = True
                logger.debug("Positive feedback saved to episode JSONL")

        # Legacy learning feedback (pattern reinforcement)
        if hasattr(self.agent, 'feedback'):
            agent_success = self.agent.feedback(positive=True, reason=reason if reason else None)
            if agent_success:
                success = True
                logger.debug("Positive feedback recorded for pattern")

        if success:
            print("\n[+] Tesekkurler! Pozitif feedback kaydedildi.")
        else:
            print("\n[!] Feedback kaydedilemedi (onceki cevap yok)")

    def _cmd_bad(self, reason: str = "") -> None:
        """
        Give negative feedback for last response.

        Args:
            reason: Optional reason for feedback
        """
        success = False

        # Episode logging feedback (JSONL update)
        if self._episode_logger:
            episode_success = self._episode_logger.add_feedback_to_last(explicit=-1.0)
            if episode_success:
                success = True
                logger.debug("Negative feedback saved to episode JSONL")

        # Legacy learning feedback (pattern reinforcement)
        if hasattr(self.agent, 'feedback'):
            agent_success = self.agent.feedback(positive=False, reason=reason if reason else None)
            if agent_success:
                success = True
                logger.debug("Negative feedback recorded for pattern")

        if success:
            print("\n[-] Tesekkurler! Negatif feedback kaydedildi.")
        else:
            print("\n[!] Feedback kaydedilemedi (onceki cevap yok)")

    def _cmd_learned(self) -> None:
        """Show number of learned patterns."""
        if not hasattr(self.agent, 'get_learned_count'):
            print("\n[Learning ozelligi mevcut degil]")
            return

        count = self.agent.get_learned_count()
        print(f"\n[Ogrenilen pattern sayisi: {count}]")

        # Show learning stats if available
        if hasattr(self.agent, 'get_learning_stats'):
            stats = self.agent.get_learning_stats()
            if stats:
                feedback_stats = stats.get('feedback', {})
                total_feedback = feedback_stats.get('total_feedback', 0)
                avg_score = feedback_stats.get('average_score', 0)
                print(f"[Toplam feedback: {total_feedback}, Ort. skor: {avg_score:.2f}]")

    def _cmd_analyze(self) -> None:
        """Run pattern analysis on episodes."""
        if not EPISODE_LOGGING_AVAILABLE:
            print("\n[Episode logging ozelligi mevcut degil]")
            return

        if not self._episode_store:
            print("\n[Episode store baslatilamadi]")
            return

        try:
            analyzer = PatternAnalyzer(self._episode_store)
            report = analyzer.generate_report()
            print("\n" + report)
        except Exception as e:
            print(f"\n[Analiz hatasi: {e}]")
            if self.show_debug:
                import traceback
                traceback.print_exc()

    def _cmd_pipeline(self, args: str = "") -> None:
        """
        Pipeline mode control.

        Args:
            args: "on", "off", or "status" (default: status)
        """
        if not hasattr(self.agent, 'set_pipeline_mode'):
            print("\n[Pipeline ozelligi mevcut degil]")
            return

        args_lower = args.lower().strip()

        if args_lower == "on":
            success = self.agent.set_pipeline_mode(True)
            if success:
                print("\n[Pipeline modu: ACIK]")
                print("[LLM yerine Thought-to-Speech Pipeline kullaniliyor]")
            else:
                print("\n[!] Pipeline acilamadi (modul mevcut degil)]")

        elif args_lower == "off":
            self.agent.set_pipeline_mode(False)
            print("\n[Pipeline modu: KAPALI]")
            print("[LLM kullaniliyor]")

        else:
            # Status
            status = self.agent.get_pipeline_status()
            enabled = status.get("enabled", False)
            available = status.get("available", False)

            print("\n--- Pipeline Durumu ---")
            print(f"  Mod: {'ACIK' if enabled else 'KAPALI'}")
            print(f"  Kullanilabilir: {'Evet' if available else 'Hayir'}")

            if status.get("pipeline_exists"):
                info = status.get("pipeline_info", {})
                config = info.get("config", {})
                print(f"  Self-critique: {'Evet' if config.get('self_critique_enabled') else 'Hayir'}")
                print(f"  Risk kontrolu: {'Evet' if config.get('risk_assessment_enabled') else 'Hayir'}")
                print(f"  Construction sayisi: {info.get('construction_count', 0)}")

            print("-----------------------")

    def _cmd_pipeinfo(self) -> None:
        """Show last pipeline processing details."""
        if not hasattr(self.agent, 'get_pipeline_debug_info'):
            print("\n[Pipeline ozelligi mevcut degil]")
            return

        debug = self.agent.get_pipeline_debug_info()

        if debug is None:
            print("\n[Pipeline henuz kullanilmadi]")
            return

        print("\n--- Son Pipeline Islemi ---")
        print(f"  Basari: {'Evet' if debug.get('success') else 'Hayir'}")
        print(f"  Cikti: {debug.get('output', 'N/A')}")

        # Situation
        if "situation" in debug:
            sit = debug["situation"]
            print(f"\n  Durum:")
            print(f"    Konu: {sit.get('topic', 'N/A')}")
            print(f"    Anlama: {sit.get('understanding', 0):.2f}")
            if "emotion" in sit:
                print(f"    Duygu: V={sit['emotion'].get('valence', 0):.2f}, A={sit['emotion'].get('arousal', 0):.2f}")
            if "intentions" in sit:
                print(f"    Niyetler: {', '.join(sit['intentions'])}")
            if "risks" in sit:
                risks = [f"{r['type']}({r['level']:.1f})" for r in sit["risks"]]
                print(f"    Riskler: {', '.join(risks)}")

        # Message plan
        if "message_plan" in debug:
            plan = debug["message_plan"]
            print(f"\n  Mesaj Plani:")
            print(f"    Acts: {', '.join(plan.get('acts', []))}")
            print(f"    Ton: {plan.get('tone', 'N/A')}")
            print(f"    Intent: {plan.get('intent', 'N/A')}")

        # Risk
        if "risk" in debug:
            risk = debug["risk"]
            print(f"\n  Risk:")
            print(f"    Seviye: {risk.get('level', 'N/A')}")
            print(f"    Skor: {risk.get('score', 0):.2f}")

        # Approval
        if "approval" in debug:
            app = debug["approval"]
            print(f"\n  Onay:")
            print(f"    Karar: {app.get('decision', 'N/A')}")
            print(f"    Onaylayan: {app.get('approver', 'N/A')}")

        # Critique
        if "critique" in debug:
            crit = debug["critique"]
            print(f"\n  Self-Critique:")
            print(f"    Gecti: {'Evet' if crit.get('passed') else 'Hayir'}")
            print(f"    Skor: {crit.get('score', 0):.2f}")
            print(f"    Ihlal: {crit.get('violations', 0)}")

        # Constructions
        if "constructions" in debug:
            print(f"\n  Kullanilan construction: {debug['constructions']}")

        print("---------------------------")

    # ===================================================================
    # IMPLICIT FEEDBACK DETECTION
    # ===================================================================

    def _detect_user_thanked(self, message: str) -> bool:
        """
        Detect if user message contains thanks.

        Args:
            message: User message text

        Returns:
            True if message contains thank patterns
        """
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in THANK_PATTERNS)

    def _detect_user_rephrased(self, current_intent: Optional[str]) -> bool:
        """
        Detect if user rephrased their message (same intent twice in a row).

        This suggests the previous response was not understood/helpful.

        Args:
            current_intent: Current message's primary intent

        Returns:
            True if current intent matches the previous intent
        """
        if current_intent and self._last_user_intent:
            return current_intent == self._last_user_intent
        return False

    def _update_implicit_feedback_for_previous(self, message: str, current_intent: Optional[str]) -> None:
        """
        Update implicit feedback for the previous episode based on current message.

        Called BEFORE processing the current message.

        Args:
            message: Current user message
            current_intent: Current message's detected intent (if available)
        """
        if not self._last_episode_id or not self._episode_logger:
            return

        implicit = ImplicitFeedback()

        # Check if user thanked (positive signal)
        if self._detect_user_thanked(message):
            implicit.user_thanked = True
            logger.debug(f"Detected user_thanked for episode {self._last_episode_id}")

        # Check if user rephrased (negative signal - not understood)
        if self._detect_user_rephrased(current_intent):
            implicit.user_rephrased = True
            logger.debug(f"Detected user_rephrased for episode {self._last_episode_id}")

        # conversation_continued is set at session end
        # session_ended_abruptly: TODO - V1'de implement edilmeyecek

        # Only update if any signal detected
        if implicit.user_thanked or implicit.user_rephrased:
            self._episode_logger.add_feedback(
                episode_id=self._last_episode_id,
                implicit=implicit
            )

    def _mark_conversation_continued(self) -> None:
        """
        Mark the last episode's conversation_continued = True.

        Called at session end (before quit) if session ended normally.
        """
        if not self._last_episode_id or not self._episode_logger:
            return

        implicit = ImplicitFeedback(conversation_continued=True)
        self._episode_logger.add_feedback(
            episode_id=self._last_episode_id,
            implicit=implicit
        )
        logger.debug(f"Marked conversation_continued for episode {self._last_episode_id}")

    def _track_intent_for_rephrase_detection(self, intent: Optional[str]) -> None:
        """
        Track intents for rephrase detection.

        Args:
            intent: Current message's primary intent
        """
        self._second_last_user_intent = self._last_user_intent
        self._last_user_intent = intent

    # ===================================================================
    # MESSAGE HANDLING
    # ===================================================================

    def _handle_message(self, message: str) -> None:
        """
        Handle user message.

        Includes implicit feedback detection for the previous episode.

        Args:
            message: User message text
        """
        # Get current intent for rephrase detection (before processing)
        current_intent = None
        if hasattr(self.agent, '_pipeline') and self.agent._pipeline:
            # Intent will be detected during processing, for now use None
            # We'll update after response
            pass

        # Update implicit feedback for PREVIOUS episode
        self._update_implicit_feedback_for_previous(message, current_intent)

        # Process the message
        response = self.agent.chat(message, self.user_id)
        self._print_response(response)

        # Track the current episode ID for next turn's implicit feedback
        if self._episode_logger and self._episode_store:
            recent = self._episode_store.get_recent(1)
            if recent:
                self._last_episode_id = recent[0].id
                # Track intent for rephrase detection
                self._track_intent_for_rephrase_detection(
                    recent[0].intent_primary.value if recent[0].intent_primary else None
                )


# ========================================================================
# ENTRY POINT
# ========================================================================

def main():
    """
    CLI entry point.

    Kullanim:
        python -m interface.chat.cli
        python -m interface.chat.cli --debug
        python -m interface.chat.cli --user my_user
        python -m interface.chat.cli --pipeline
    """
    parser = argparse.ArgumentParser(
        description="UEM Chat CLI - Terminal tabanli chat arayuzu"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Debug modunu ac"
    )
    parser.add_argument(
        "--user", "-u",
        default="cli_user",
        help="Kullanici ID (default: cli_user)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Mock LLM kullan (test icin)"
    )
    parser.add_argument(
        "--pipeline", "-p",
        action="store_true",
        help="Pipeline modunda baslat (LLM yerine Thought-to-Speech Pipeline)"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=log_level)

    try:
        # Create config with pipeline option
        from core.language import ChatConfig
        # Enable pipeline if requested OR if episode logging is available (required for context tracking)
        use_pipeline = args.pipeline or EPISODE_LOGGING_AVAILABLE
        config = ChatConfig(use_pipeline=use_pipeline)

        # Create agent
        if args.mock and UEM_AVAILABLE:
            from core.language import MockLLMAdapter
            agent = UEMChatAgent(config=config, llm=MockLLMAdapter())
        else:
            agent = UEMChatAgent(config=config)

        # Create and start CLI
        cli = CLIChat(
            agent=agent,
            user_id=args.user,
            show_debug=args.debug,
        )

        # Print pipeline status at start
        if args.pipeline:
            print("[Pipeline modu ACIK - LLM kullanilmiyor]")

        cli.start()

    except KeyboardInterrupt:
        print("\n\nCikis yapiliyor...")
        sys.exit(0)
    except ImportError as e:
        print(f"Hata: Gerekli moduller yuklenemedi: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Hata: {e}")
        if args.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
