"""Enhanced base classes for LLM implementations with shared functionality."""

import json
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List

from .api import PRTAPI
from .config import LLMConfigManager
from .llm_prompts import LLMPromptGenerator
from .llm_tools import LLMToolRegistry
from .llm_tools import Tool
from .logging_config import get_logger

logger = get_logger(__name__)


class BaseLLM(ABC):
    """Enhanced base class with shared functionality and protocol abstraction."""

    def __init__(self, api: PRTAPI, config_manager: LLMConfigManager):
        """Initialize base LLM with API and config manager.

        Args:
            api: PRT API instance for database operations
            config_manager: LLM configuration manager
        """
        self.api = api
        self.config_manager = config_manager

        # Initialize tool registry and prompt generator
        disabled_tools_list = getattr(config_manager.tools, "disabled_tools", [])
        disabled_tools_set = set(disabled_tools_list) if disabled_tools_list else set()
        self.tool_registry = LLMToolRegistry(api, disabled_tools_set)
        self.tools = self.tool_registry.get_all_tools()
        self.prompt_generator = LLMPromptGenerator(self.tools)

        self.conversation_history = []

    @abstractmethod
    def _send_message_with_tools(self, messages: List[Dict], tools: List[Tool]) -> Any:
        """Send message with tools to provider (protocol-specific implementation).

        Args:
            messages: Message history in provider format
            tools: Available tools

        Returns:
            Provider-specific response
        """

    @abstractmethod
    def _extract_tool_calls(self, response: Any) -> List[Dict]:
        """Extract tool calls from provider response.

        Args:
            response: Provider-specific response

        Returns:
            List of tool call dictionaries
        """

    def chat(self, message: str) -> str:
        """Unified chat logic with protocol-specific delegation.

        Args:
            message: User message

        Returns:
            LLM response
        """
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})

        try:
            # Create system prompt using shared generator
            system_prompt = self.prompt_generator.create_system_prompt(
                provider=self._get_provider_name(),
                schema_detail="essential",
                model=self._get_model_name(),
            )

            # Prepare messages for provider
            messages = [{"role": "system", "content": system_prompt}] + self.conversation_history

            # Send to provider (protocol-specific)
            response = self._send_message_with_tools(messages, self.tools)

            # Extract tool calls (protocol-specific)
            tool_calls = self._extract_tool_calls(response)

            # Fallback: Check for tool suggestions in content (for models like Mistral)
            if not tool_calls:
                assistant_content = self._extract_assistant_message(response)
                suggested_tools = self._detect_tool_suggestions(assistant_content)
                if suggested_tools:
                    logger.info(
                        f"[LLM] Detected {len(suggested_tools)} tool suggestions in content, executing them"
                    )
                    tool_calls = suggested_tools

            # Execute tool calls using shared logic
            if tool_calls:
                tool_results = []
                for tool_call in tool_calls:
                    result = self._call_tool(tool_call["name"], tool_call.get("arguments", {}))
                    tool_results.append(
                        {
                            "tool_call_id": tool_call.get("id", ""),
                            "name": tool_call["name"],
                            "result": result,
                        }
                    )

                # Add tool results to conversation
                self._add_tool_results_to_history(tool_calls, tool_results)

                # Get final response
                final_messages = [
                    {"role": "system", "content": system_prompt}
                ] + self.conversation_history
                final_response = self._send_message_with_tools(final_messages, self.tools)
                assistant_message = self._extract_assistant_message(final_response)
            else:
                # No tool calls, extract direct response
                assistant_message = self._extract_assistant_message(response)

            # Add assistant response to history
            if assistant_message:
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )
            else:
                # Handle empty response
                logger.warning("[LLM] Received empty response content")
                assistant_message = "I received your message but didn't generate a response. Please try rephrasing your question."
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )

            return assistant_message

        except Exception as e:
            logger.error(f"[LLM] Error in chat: {e}")
            return f"Error: {e}"

    @abstractmethod
    def _get_provider_name(self) -> str:
        """Get provider name for prompt generation.

        Returns:
            Provider name string (e.g., "ollama", "llamacpp")
        """

    @abstractmethod
    def _get_model_name(self) -> str:
        """Get model name for model-specific prompt customizations.

        Returns:
            Model name string (e.g., "mistral:7b-instruct", "gpt-oss:20b")
        """

    @abstractmethod
    def _extract_assistant_message(self, response: Any) -> str:
        """Extract assistant message from provider response.

        Args:
            response: Provider-specific response

        Returns:
            Assistant message text
        """

    def _add_tool_results_to_history(self, tool_calls: List[Dict], tool_results: List[Dict]):
        """Add tool calls and results to conversation history.

        Args:
            tool_calls: Tool call information
            tool_results: Tool execution results
        """
        # Add tool calls message
        self.conversation_history.append({"role": "assistant", "tool_calls": tool_calls})

        # Add tool results
        for tool_result in tool_results:
            self.conversation_history.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": json.dumps(tool_result["result"], default=self._json_serializer),
                }
            )

    def _json_serializer(self, obj: Any) -> Any:
        """Shared JSON serializer for tool arguments.

        Args:
            obj: Object to serialize

        Returns:
            JSON-serializable representation
        """
        if isinstance(obj, bytes):
            # Convert bytes to a safe string representation for LLM consumption
            return f"<binary data: {len(obj)} bytes>"
        elif hasattr(obj, "isoformat"):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        else:
            return str(obj)

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("[LLM] Conversation history cleared")

    def _get_tool_by_name(self, tool_name: str) -> Tool:
        """Get tool by name using registry.

        Args:
            tool_name: Name of tool to find

        Returns:
            Tool object or None if not found
        """
        return self.tool_registry.get_tool_by_name(tool_name)

    def _is_write_operation(self, tool_name: str) -> bool:
        """Check if tool is a write operation using registry.

        Args:
            tool_name: Name of tool to check

        Returns:
            True if tool modifies data
        """
        return tool_name in LLMToolRegistry.get_write_tool_names()

    def _safe_write_wrapper(self, tool_name: str, tool_function: Any, **arguments) -> Any:
        """Wrapper for write operations with automatic backup.

        Args:
            tool_name: Name of tool being called
            tool_function: Tool function to call
            **arguments: Tool arguments

        Returns:
            Tool result with backup information
        """
        try:
            # Auto-backup before write operations (except manual backups)
            if tool_name != "create_backup_with_comment":
                backup_result = self.api.create_backup_with_comment(
                    f"Auto-backup before {tool_name}"
                )
                logger.info(f"[LLM] Auto-backup created: {backup_result}")

            # Execute the operation
            result = tool_function(**arguments)

            # Add backup info to result
            if isinstance(result, dict) and tool_name != "create_backup_with_comment":
                result["backup_created"] = backup_result.get("backup_id", "unknown")

            return result

        except Exception as e:
            logger.error(f"[LLM] Error in safe write operation {tool_name}: {e}")
            return {"error": f"Error in {tool_name}: {str(e)}"}

    def _detect_tool_suggestions(self, content: str) -> List[Dict]:
        """Detect tool suggestions in assistant content (fallback for models like Mistral).

        Args:
            content: Assistant response content

        Returns:
            List of tool call dictionaries in standard format
        """
        import re

        tool_calls = []
        available_tool_names = {tool.name for tool in self.tools}

        # Pattern 1: Look for tool mentions like "use search_contacts" or "call get_database_stats"
        tool_mention_patterns = [
            r"(?:use|call|execute)\s+`?(\w+)`?(?:\s*\(([^)]*)\))?",
            r"`(\w+)`?\s*(?:function|tool)(?:\s*\(([^)]*)\))?",
            r"(\w+)(?:\s*\([^)]*\))?\s*(?:function|tool)",
        ]

        for pattern in tool_mention_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                tool_name = match.group(1)
                if tool_name in available_tool_names:
                    # Try to extract arguments if provided
                    args = {}
                    if len(match.groups()) > 1 and match.group(2):
                        try:
                            # Simple argument parsing for common cases
                            args_str = match.group(2).strip()
                            if (
                                args_str
                                and not args_str.isspace()
                                and args_str.startswith('"')
                                and args_str.endswith('"')
                                and tool_name == "search_contacts"
                            ):
                                # Assume it's a query string
                                args = {"query": args_str.strip('"')}
                        except Exception:
                            pass  # Use empty args if parsing fails

                    tool_calls.append(
                        {"id": f"detected_{len(tool_calls)}", "name": tool_name, "arguments": args}
                    )
                    logger.info(f"[LLM] Detected tool suggestion: {tool_name} with args: {args}")

        # Pattern 2: Specific heuristics for common queries
        if not tool_calls:
            content_lower = content.lower()

            # "How many contacts" -> get_database_stats
            if (
                any(
                    phrase in content_lower
                    for phrase in ["how many contacts", "count contacts", "number of contacts"]
                )
                and "get_database_stats" in available_tool_names
            ):
                tool_calls.append(
                    {"id": "detected_count", "name": "get_database_stats", "arguments": {}}
                )
                logger.info("[LLM] Detected count request -> get_database_stats")

            # "Find [term]" -> search_contacts
            find_match = re.search(r"find\s+(\w+)", content_lower)
            if find_match and "search_contacts" in available_tool_names:
                search_term = find_match.group(1)
                tool_calls.append(
                    {
                        "id": "detected_search",
                        "name": "search_contacts",
                        "arguments": {"query": search_term},
                    }
                )
                logger.info(f"[LLM] Detected search request -> search_contacts('{search_term}')")

        return tool_calls

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with the given arguments using shared logic.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Tool result
        """
        tool = self._get_tool_by_name(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            # Handle special cases
            if tool_name == "search_contacts" and "query" not in arguments:
                arguments["query"] = ""

            # Use safe wrapper for write operations
            if self._is_write_operation(tool_name):
                return self._safe_write_wrapper(tool_name, tool.function, **arguments)

            # Execute read-only operations directly
            return tool.function(**arguments)

        except Exception as e:
            logger.error(f"[LLM] Error calling tool '{tool_name}': {e}")
            return {"error": f"Error calling tool '{tool_name}': {e}"}
