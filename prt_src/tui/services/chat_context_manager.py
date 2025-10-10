"""ChatContextManager - Manages conversation history for LLM chat.

Handles:
- Storing conversation messages (user, assistant, system)
- Automatic pruning when history exceeds max_history
- Preserving system prompts during pruning
- Preparing messages for LLM API calls
"""

from typing import Dict
from typing import List
from typing import Optional


class ChatContextManager:
    """Manages conversation history and context for LLM chat.

    Attributes:
        max_history: Maximum number of messages to keep
        messages: List of message dicts with 'role' and 'content' keys
    """

    def __init__(self, max_history: int = 50):
        """Initialize chat context manager.

        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []

    def add_user_message(self, content: str) -> None:
        """Add a user message to history.

        Args:
            content: User's message content
        """
        self.messages.append({"role": "user", "content": content})
        self._prune_if_needed()

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant (LLM) message to history.

        Args:
            content: Assistant's message content
        """
        self.messages.append({"role": "assistant", "content": content})
        self._prune_if_needed()

    def add_system_message(self, content: str) -> None:
        """Add a system message to history.

        Args:
            content: System message content
        """
        self.messages.append({"role": "system", "content": content})
        self._prune_if_needed()

    def get_messages_for_llm(self, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Get messages formatted for LLM API call.

        Args:
            system_prompt: Optional system prompt to prepend

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        if system_prompt:
            return [{"role": "system", "content": system_prompt}] + self.messages
        return self.messages.copy()

    def clear_history(self) -> None:
        """Clear all messages from history."""
        self.messages = []

    def get_last_user_message(self) -> Optional[Dict[str, str]]:
        """Get the last user message from history.

        Returns:
            Last user message dict, or None if no user messages
        """
        for message in reversed(self.messages):
            if message["role"] == "user":
                return message
        return None

    def message_count(self) -> int:
        """Get count of messages in history.

        Returns:
            Number of messages
        """
        return len(self.messages)

    def _prune_if_needed(self) -> None:
        """Prune old messages if history exceeds max_history.

        Preserves the first system message (if present) and keeps the most recent messages.
        """
        if len(self.messages) <= self.max_history:
            return

        # Check if first message is a system prompt
        has_system_prompt = len(self.messages) > 0 and self.messages[0]["role"] == "system"

        if has_system_prompt:
            # Keep system prompt + most recent (max_history - 1) messages
            system_prompt = self.messages[0]
            recent_messages = self.messages[-(self.max_history - 1) :]
            self.messages = [system_prompt] + recent_messages
        else:
            # Keep most recent max_history messages
            self.messages = self.messages[-self.max_history :]
