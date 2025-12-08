"""
tests/unit/test_cli_chat.py

CLIChat unit testleri.
Terminal chat arayuzu testleri.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from io import StringIO
import sys

from interface.chat.cli import CLIChat, main


# ========================================================================
# MOCK CLASSES
# ========================================================================

class MockChatResponse:
    """Mock ChatResponse for testing."""

    def __init__(
        self,
        content: str = "Test response",
        emotion=None,
        intent: str = None,
        llm_response=None,
    ):
        self.content = content
        self.emotion = emotion
        self.intent = intent
        self.llm_response = llm_response


class MockEmotion:
    """Mock PADState for testing."""

    def __init__(self, pleasure: float = 0.5, arousal: float = 0.5):
        self.pleasure = pleasure
        self.valence = pleasure
        self.arousal = arousal


class MockLLMResponse:
    """Mock LLMResponse for testing."""

    def __init__(self, latency_ms: float = 100):
        self.latency_ms = latency_ms


class MockAgent:
    """Mock UEMChatAgent for testing."""

    def __init__(self):
        self._session_started = False
        self._session_ended = False
        self._messages = []
        self._recall_results = []
        self._history = []

    def start_session(self, user_id: str) -> str:
        self._session_started = True
        return f"session_{user_id}"

    def end_session(self, user_id: str = None) -> None:
        self._session_ended = True

    def chat(self, message: str, user_id: str = None) -> MockChatResponse:
        self._messages.append(message)
        return MockChatResponse(content=f"Response to: {message}")

    def recall(self, query: str, k: int = 5):
        return self._recall_results[:k]

    def get_conversation_history(self, n: int = 10):
        return self._history[:n]

    def get_session_stats(self):
        return {
            "session_id": "test_session",
            "user_id": "test_user",
            "turn_count": len(self._messages),
            "total_sessions": 1,
            "total_turns": len(self._messages),
            "average_emotion": {"pleasure": 0.5},
        }


# ========================================================================
# FIXTURES
# ========================================================================

@pytest.fixture
def mock_agent():
    """Mock agent for testing."""
    return MockAgent()


@pytest.fixture
def cli_chat(mock_agent):
    """CLIChat with mock agent."""
    return CLIChat(agent=mock_agent, user_id="test_user", show_debug=False)


@pytest.fixture
def debug_cli_chat(mock_agent):
    """CLIChat with debug mode."""
    return CLIChat(agent=mock_agent, user_id="test_user", show_debug=True)


# ========================================================================
# INIT TESTS
# ========================================================================

class TestCLIChatInit:
    """CLIChat initialization testleri."""

    def test_cli_init(self, mock_agent):
        """Default init calismali."""
        cli = CLIChat(agent=mock_agent)
        assert cli.agent is mock_agent
        assert cli.user_id == "cli_user"
        assert cli.show_debug is False
        assert cli._running is False

    def test_cli_init_with_custom_user(self, mock_agent):
        """Custom user ID ile init calismali."""
        cli = CLIChat(agent=mock_agent, user_id="custom_user")
        assert cli.user_id == "custom_user"

    def test_cli_init_with_debug(self, mock_agent):
        """Debug mode ile init calismali."""
        cli = CLIChat(agent=mock_agent, show_debug=True)
        assert cli.show_debug is True

    def test_cli_init_with_custom_agent(self, mock_agent):
        """Custom agent ile init calismali."""
        cli = CLIChat(agent=mock_agent)
        assert cli.agent is mock_agent


# ========================================================================
# COMMAND DETECTION TESTS
# ========================================================================

class TestIsCommand:
    """_is_command() testleri."""

    def test_is_command_slash(self, cli_chat):
        """/ ile baslayan komut olmali."""
        assert cli_chat._is_command("/help") is True
        assert cli_chat._is_command("/quit") is True
        assert cli_chat._is_command("/stats") is True

    def test_is_command_normal_text(self, cli_chat):
        """Normal metin komut olmamali."""
        assert cli_chat._is_command("hello") is False
        assert cli_chat._is_command("merhaba") is False
        assert cli_chat._is_command("test message") is False

    def test_is_command_empty(self, cli_chat):
        """Bos metin komut olmamali."""
        assert cli_chat._is_command("") is False


# ========================================================================
# COMMAND HANDLER TESTS
# ========================================================================

class TestHandleHelpCommand:
    """Help command testleri."""

    def test_handle_help_command(self, cli_chat, capsys):
        """/help komutu yardim mesaji gostermeli."""
        cli_chat._handle_command("/help")
        captured = capsys.readouterr()
        assert "Komutlar" in captured.out
        assert "/help" in captured.out
        assert "/quit" in captured.out

    def test_handle_help_short(self, cli_chat, capsys):
        """/h komutu da calismali."""
        cli_chat._handle_command("/h")
        captured = capsys.readouterr()
        assert "Komutlar" in captured.out


class TestHandleQuitCommand:
    """Quit command testleri."""

    def test_handle_quit_command(self, cli_chat):
        """/quit komutu _running'i False yapmali."""
        cli_chat._running = True
        cli_chat._handle_command("/quit")
        assert cli_chat._running is False

    def test_handle_exit_command(self, cli_chat):
        """/exit komutu da calismali."""
        cli_chat._running = True
        cli_chat._handle_command("/exit")
        assert cli_chat._running is False

    def test_handle_q_command(self, cli_chat):
        """/q komutu da calismali."""
        cli_chat._running = True
        cli_chat._handle_command("/q")
        assert cli_chat._running is False


class TestHandleHistoryCommand:
    """History command testleri."""

    def test_handle_history_command_empty(self, cli_chat, capsys):
        """/history bos gecmis gostermeli."""
        cli_chat._handle_command("/history")
        captured = capsys.readouterr()
        assert "bos" in captured.out.lower()

    def test_handle_history_command_with_data(self, cli_chat, mock_agent, capsys):
        """/history mesajlari gostermeli."""
        mock_agent._history = [
            {"role": "user", "content": "Hello"},
            {"role": "agent", "content": "Hi there"},
        ]
        cli_chat._handle_command("/history")
        captured = capsys.readouterr()
        assert "Hello" in captured.out or "Mesaj" in captured.out


class TestHandleRecallCommand:
    """Recall command testleri."""

    def test_handle_recall_command_no_query(self, cli_chat, capsys):
        """/recall sorgu olmadan hata vermeli."""
        cli_chat._handle_command("/recall")
        captured = capsys.readouterr()
        assert "Kullanim" in captured.out or "recall" in captured.out.lower()

    def test_handle_recall_command_with_query(self, cli_chat, mock_agent, capsys):
        """/recall sorgu ile arama yapmali."""
        mock_agent._recall_results = [
            MagicMock(content="Memory 1", similarity=0.9),
            MagicMock(content="Memory 2", similarity=0.8),
        ]
        cli_chat._handle_command("/recall test query")
        captured = capsys.readouterr()
        assert "Memory" in captured.out or "Ani" in captured.out

    def test_handle_recall_no_results(self, cli_chat, mock_agent, capsys):
        """/recall sonuc bulunamazsa mesaj vermeli."""
        mock_agent._recall_results = []
        cli_chat._handle_command("/recall nonexistent")
        captured = capsys.readouterr()
        assert "bulunamadi" in captured.out.lower()


class TestHandleStatsCommand:
    """Stats command testleri."""

    def test_handle_stats_command(self, cli_chat, capsys):
        """/stats istatistikleri gostermeli."""
        cli_chat._handle_command("/stats")
        captured = capsys.readouterr()
        assert "Session" in captured.out or "Istatistik" in captured.out
        assert "turn" in captured.out.lower() or "Turn" in captured.out


class TestHandleDebugCommand:
    """Debug command testleri."""

    def test_handle_debug_command_toggle_on(self, cli_chat, capsys):
        """/debug modunu acmali."""
        cli_chat.show_debug = False
        cli_chat._handle_command("/debug")
        assert cli_chat.show_debug is True
        captured = capsys.readouterr()
        assert "ACIK" in captured.out or "debug" in captured.out.lower()

    def test_handle_debug_command_toggle_off(self, cli_chat, capsys):
        """/debug modunu kapatmali."""
        cli_chat.show_debug = True
        cli_chat._handle_command("/debug")
        assert cli_chat.show_debug is False
        captured = capsys.readouterr()
        assert "KAPALI" in captured.out or "debug" in captured.out.lower()


class TestHandleClearCommand:
    """Clear command testleri."""

    def test_handle_clear_command(self, cli_chat):
        """/clear komutu hata vermemeli."""
        # Just ensure it doesn't crash
        with patch('os.system') as mock_system:
            cli_chat._handle_command("/clear")
            mock_system.assert_called_once()


class TestHandleUnknownCommand:
    """Unknown command testleri."""

    def test_handle_unknown_command(self, cli_chat, capsys):
        """Bilinmeyen komut mesaji gostermeli."""
        cli_chat._handle_command("/unknown")
        captured = capsys.readouterr()
        assert "Bilinmeyen" in captured.out or "unknown" in captured.out.lower()


# ========================================================================
# MESSAGE HANDLING TESTS
# ========================================================================

class TestHandleMessage:
    """_handle_message() testleri."""

    def test_handle_message(self, cli_chat, mock_agent, capsys):
        """Mesaj gonderilmeli ve yanit alinmali."""
        cli_chat._handle_message("Hello!")
        assert "Hello!" in mock_agent._messages
        captured = capsys.readouterr()
        assert "Response to: Hello!" in captured.out

    def test_handle_message_turkish(self, cli_chat, mock_agent, capsys):
        """Turkce mesaj calismali."""
        cli_chat._handle_message("Merhaba!")
        assert "Merhaba!" in mock_agent._messages


# ========================================================================
# OUTPUT TESTS
# ========================================================================

class TestPrintResponse:
    """_print_response() testleri."""

    def test_print_response_basic(self, cli_chat, capsys):
        """Basic response yazilmali."""
        response = MockChatResponse(content="Test response")
        cli_chat._print_response(response)
        captured = capsys.readouterr()
        assert "Test response" in captured.out

    def test_print_response_with_debug(self, debug_cli_chat, capsys):
        """Debug modunda ekstra bilgi yazilmali."""
        response = MockChatResponse(
            content="Test response",
            emotion=MockEmotion(pleasure=0.7, arousal=0.5),
            intent="greeting",
            llm_response=MockLLMResponse(latency_ms=150),
        )
        debug_cli_chat._print_response(response)
        captured = capsys.readouterr()
        assert "Test response" in captured.out
        assert "Debug" in captured.out or "0.7" in captured.out


class TestWelcomeGoodbye:
    """Welcome ve goodbye mesaj testleri."""

    def test_print_welcome(self, cli_chat, capsys):
        """Welcome mesaji yazilmali."""
        cli_chat._print_welcome()
        captured = capsys.readouterr()
        assert "UEM" in captured.out
        assert "Merhaba" in captured.out or "Chat" in captured.out

    def test_print_goodbye(self, cli_chat, capsys):
        """Goodbye mesaji yazilmali."""
        cli_chat._print_goodbye()
        captured = capsys.readouterr()
        assert "Gorusuruz" in captured.out or "gunler" in captured.out.lower()


# ========================================================================
# STOP TESTS
# ========================================================================

class TestStop:
    """stop() testleri."""

    def test_stop(self, cli_chat, mock_agent):
        """Stop session'i kapatmali."""
        cli_chat._running = True
        cli_chat.stop()
        assert cli_chat._running is False
        assert mock_agent._session_ended is True


# ========================================================================
# MAIN FUNCTION TESTS
# ========================================================================

class TestMain:
    """main() function testleri."""

    def test_main_with_mock_flag(self):
        """--mock flag calismali."""
        with patch('sys.argv', ['cli.py', '--mock']):
            with patch.object(CLIChat, 'start') as mock_start:
                # Mock start to avoid infinite loop
                mock_start.side_effect = KeyboardInterrupt()
                try:
                    main()
                except SystemExit:
                    pass

    def test_main_with_debug_flag(self):
        """--debug flag calismali."""
        with patch('sys.argv', ['cli.py', '--debug', '--mock']):
            with patch.object(CLIChat, 'start') as mock_start:
                mock_start.side_effect = KeyboardInterrupt()
                try:
                    main()
                except SystemExit:
                    pass

    def test_main_with_user_flag(self):
        """--user flag calismali."""
        with patch('sys.argv', ['cli.py', '--user', 'custom_user', '--mock']):
            with patch.object(CLIChat, 'start') as mock_start:
                mock_start.side_effect = KeyboardInterrupt()
                try:
                    main()
                except SystemExit:
                    pass


# ========================================================================
# INPUT TESTS
# ========================================================================

class TestGetInput:
    """_get_input() testleri."""

    def test_get_input_normal(self, cli_chat):
        """Normal input alinabilmeli."""
        with patch('builtins.input', return_value="test input"):
            result = cli_chat._get_input()
            assert result == "test input"

    def test_get_input_keyboard_interrupt(self, cli_chat):
        """Ctrl+C None dondurmeli ve stop etmeli."""
        cli_chat._running = True
        with patch('builtins.input', side_effect=KeyboardInterrupt()):
            result = cli_chat._get_input()
            assert result is None
            assert cli_chat._running is False

    def test_get_input_eof(self, cli_chat):
        """EOF None dondurmeli."""
        cli_chat._running = True
        with patch('builtins.input', side_effect=EOFError()):
            result = cli_chat._get_input()
            assert result is None
