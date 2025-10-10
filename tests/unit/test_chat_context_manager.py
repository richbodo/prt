"""Unit tests for ChatContextManager.

Tests conversation history management and LLM context preparation.
"""

import pytest


class TestChatContextManagerBasic:
    """Test basic ChatContextManager functionality."""

    @pytest.mark.unit
    def test_context_manager_instantiates(self):
        """ChatContextManager can be instantiated."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()
        assert manager is not None
        assert manager.max_history == 50
        assert len(manager.messages) == 0

    @pytest.mark.unit
    def test_context_manager_with_custom_max_history(self):
        """ChatContextManager can be instantiated with custom max_history."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager(max_history=100)
        assert manager.max_history == 100


class TestConversationHistory:
    """Test conversation history management."""

    @pytest.mark.unit
    def test_add_user_message(self):
        """Can add user message to history."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()
        manager.add_user_message("search for tech contacts")

        assert len(manager.messages) == 1
        assert manager.messages[0]["role"] == "user"
        assert manager.messages[0]["content"] == "search for tech contacts"

    @pytest.mark.unit
    def test_add_assistant_message(self):
        """Can add assistant message to history."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()
        manager.add_assistant_message('{"intent": "search", "parameters": {}}')

        assert len(manager.messages) == 1
        assert manager.messages[0]["role"] == "assistant"
        assert '"intent": "search"' in manager.messages[0]["content"]

    @pytest.mark.unit
    def test_add_system_message(self):
        """Can add system message to history."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()
        manager.add_system_message("Found 5 contacts matching your query")

        assert len(manager.messages) == 1
        assert manager.messages[0]["role"] == "system"
        assert "Found 5 contacts" in manager.messages[0]["content"]

    @pytest.mark.unit
    def test_conversation_flow(self):
        """Can build up conversation with multiple messages."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()

        # User asks
        manager.add_user_message("show me tech contacts")
        # LLM responds
        manager.add_assistant_message('{"intent": "search"}')
        # System confirms
        manager.add_system_message("Found 3 contacts")
        # User refines
        manager.add_user_message("just the ones in SF")

        assert len(manager.messages) == 4
        assert manager.messages[0]["role"] == "user"
        assert manager.messages[1]["role"] == "assistant"
        assert manager.messages[2]["role"] == "system"
        assert manager.messages[3]["role"] == "user"


class TestHistoryPruning:
    """Test automatic history pruning when max_history reached."""

    @pytest.mark.unit
    def test_prune_when_exceeds_max_history(self):
        """Old messages are pruned when max_history exceeded."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager(max_history=5)

        # Add 7 messages
        for i in range(7):
            manager.add_user_message(f"message {i}")

        # Should only keep last 5
        assert len(manager.messages) == 5
        assert manager.messages[0]["content"] == "message 2"
        assert manager.messages[-1]["content"] == "message 6"

    @pytest.mark.unit
    def test_preserve_system_prompt_when_pruning(self):
        """System prompt (first message) is preserved when pruning."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager(max_history=5)

        # Add initial system prompt
        manager.add_system_message("You are a helpful assistant")

        # Add many user messages
        for i in range(10):
            manager.add_user_message(f"message {i}")

        # Should keep system prompt + last 4 messages
        assert len(manager.messages) == 5
        assert manager.messages[0]["role"] == "system"
        assert manager.messages[0]["content"] == "You are a helpful assistant"
        assert manager.messages[-1]["content"] == "message 9"


class TestContextPreparation:
    """Test preparing context for LLM calls."""

    @pytest.mark.unit
    def test_get_messages_for_llm(self):
        """Can get messages formatted for LLM."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()
        manager.add_user_message("search contacts")
        manager.add_assistant_message('{"intent": "search"}')

        messages = manager.get_messages_for_llm()

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    @pytest.mark.unit
    def test_get_messages_with_system_prompt(self):
        """Can prepend system prompt when getting messages."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()
        manager.add_user_message("search contacts")

        system_prompt = "You are a database assistant"
        messages = manager.get_messages_for_llm(system_prompt=system_prompt)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == system_prompt
        assert messages[1]["role"] == "user"


class TestUtilityMethods:
    """Test utility methods."""

    @pytest.mark.unit
    def test_clear_history(self):
        """Can clear conversation history."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()
        manager.add_user_message("message 1")
        manager.add_user_message("message 2")

        assert len(manager.messages) == 2

        manager.clear_history()

        assert len(manager.messages) == 0

    @pytest.mark.unit
    def test_get_last_user_message(self):
        """Can get last user message."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()
        manager.add_user_message("first message")
        manager.add_assistant_message("response")
        manager.add_user_message("second message")

        last_msg = manager.get_last_user_message()

        assert last_msg is not None
        assert last_msg["content"] == "second message"

    @pytest.mark.unit
    def test_get_last_user_message_when_empty(self):
        """get_last_user_message returns None when no messages."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()

        last_msg = manager.get_last_user_message()

        assert last_msg is None

    @pytest.mark.unit
    def test_message_count(self):
        """Can get message count."""
        from prt_src.tui.services.chat_context_manager import ChatContextManager

        manager = ChatContextManager()

        assert manager.message_count() == 0

        manager.add_user_message("message 1")
        manager.add_user_message("message 2")

        assert manager.message_count() == 2
