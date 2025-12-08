"""
interface/chat/cli.py

CLI Chat Interface - Terminal tabanli UEM chat.
UEM v2 - Interaktif sohbet arayuzu.

Ozellikler:
- Interaktif chat loop
- Komut destegi (/help, /quit, /history, /recall, /stats, /debug, /clear)
- Debug modu
- Session yonetimi
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
    UEM_AVAILABLE = True
except ImportError:
    UEM_AVAILABLE = False

logger = logging.getLogger(__name__)


class CLIChat:
    """
    CLI Chat Interface.

    Terminal tabanli interaktif UEM chat arayuzu.

    Kullanim:
        cli = CLIChat()
        cli.start()

    Komutlar:
        /help    - Komutlari goster
        /quit    - Cikis
        /exit    - Cikis
        /history - Son 10 mesaji goster
        /recall  - Ani ara (semantic search)
        /stats   - Session istatistikleri
        /debug   - Debug modunu ac/kapat
        /clear   - Ekrani temizle
        /good, /+ - Pozitif feedback
        /bad, /-  - Negatif feedback
        /learned  - Ogrenilen pattern sayisi
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
        """
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

        Returns:
            User input string or None if interrupted
        """
        try:
            return input("\nSen: ").strip()
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
        print("----------------")

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
        if not hasattr(self.agent, 'feedback'):
            print("\n[Feedback ozelligi mevcut degil]")
            return

        success = self.agent.feedback(positive=True, reason=reason if reason else None)
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
        if not hasattr(self.agent, 'feedback'):
            print("\n[Feedback ozelligi mevcut degil]")
            return

        success = self.agent.feedback(positive=False, reason=reason if reason else None)
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

    # ===================================================================
    # MESSAGE HANDLING
    # ===================================================================

    def _handle_message(self, message: str) -> None:
        """
        Handle user message.

        Args:
            message: User message text
        """
        response = self.agent.chat(message, self.user_id)
        self._print_response(response)


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

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=log_level)

    try:
        # Create agent
        if args.mock and UEM_AVAILABLE:
            from core.language import MockLLMAdapter
            agent = UEMChatAgent(llm=MockLLMAdapter())
        else:
            agent = None  # Will create default

        # Create and start CLI
        cli = CLIChat(
            agent=agent,
            user_id=args.user,
            show_debug=args.debug,
        )
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
