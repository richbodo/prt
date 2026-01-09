"""
LlamaCpp LLM Integration for PRT

This module provides integration with llama-cpp-python for running local GGUF models
with tool calling capabilities for PRT operations.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from llama_cpp import Llama

from .api import PRTAPI
from .config import LLMConfigManager
from .llm_base import BaseLLM
from .llm_tools import Tool
from .logging_config import get_logger

logger = get_logger(__name__)


class LlamaCppLLM(BaseLLM):
    """LlamaCpp LLM client with tool calling support."""

    def __init__(
        self,
        api: PRTAPI,
        model_path: str | None = None,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
        n_threads: int | None = None,
        timeout: int | None = None,
        config_manager: LLMConfigManager | None = None,
    ):
        """Initialize LlamaCpp LLM client.

        Args:
            api: PRTAPI instance for database operations
            model_path: Path to .gguf model file
            n_ctx: Context window size (default: 4096)
            n_gpu_layers: Number of layers to offload to GPU (default: 0 = CPU only)
            n_threads: Number of CPU threads (default: None = auto-detect)
            timeout: Request timeout in seconds
            config_manager: LLMConfigManager instance. If None, loads config automatically.
        """
        # Load configuration
        if config_manager is None:
            config_manager = LLMConfigManager()

        # Call parent constructor (gets tools automatically from registry)
        super().__init__(api, config_manager)

        # Use config values, falling back to explicit parameters
        self.model_path = model_path or config_manager.llm.model_path
        self.n_ctx = n_ctx if n_ctx != 4096 else getattr(config_manager.llm, "n_ctx", 4096)
        self.n_gpu_layers = (
            n_gpu_layers if n_gpu_layers != 0 else getattr(config_manager.llm, "n_gpu_layers", 0)
        )
        self.n_threads = n_threads or getattr(config_manager.llm, "n_threads", None)
        self.timeout = timeout if timeout is not None else config_manager.llm.timeout
        self.temperature = config_manager.llm.temperature

        # Validate model path
        if not self.model_path:
            raise ValueError("model_path is required for LlamaCpp provider")

        model_file = Path(self.model_path)
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        # Extract friendly model name for display (filename without extension)
        self.model = model_file.stem  # e.g., "Meta-Llama-3-8B-Instruct-Q4_K_M"

        # Initialize llama-cpp-python
        logger.info(f"[LLM] Loading model from {self.model_path}")
        logger.info(
            f"[LLM] Config: n_ctx={self.n_ctx}, n_gpu_layers={self.n_gpu_layers}, "
            f"n_threads={self.n_threads}, timeout={self.timeout}s"
        )

        try:
            self.llm = Llama(
                model_path=str(model_file),
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
                verbose=False,  # Reduce noise in logs
            )
            logger.info("[LLM] Model loaded successfully")
        except Exception as e:
            logger.error(f"[LLM] Failed to load model: {e}")
            raise RuntimeError(f"Failed to load LlamaCpp model: {e}") from e

        # Tools and conversation history are now initialized by parent class
        logger.info(
            f"[LLM] Initialized LlamaCppLLM: model={model_file.name}, "
            f"n_ctx={self.n_ctx}, timeout={self.timeout}s, tools={len(self.tools)}"
        )

    async def health_check(self, timeout: float = 2.0) -> bool:
        """Quick health check to see if the model is loaded and responsive.

        Args:
            timeout: Timeout in seconds for the health check

        Returns:
            True if model is available and responsive, False otherwise
        """
        logger.debug(f"[LLM] Starting health check (timeout={timeout}s)")
        try:
            # Try a simple completion to verify model works
            logger.debug("[LLM] Running test completion...")
            result = await asyncio.to_thread(
                self.llm.create_completion,
                prompt="Hi",
                max_tokens=1,
                temperature=0.0,
            )
            is_healthy = result is not None and "choices" in result
            logger.info(f"[LLM] Health check result: {'PASS' if is_healthy else 'FAIL'}")
            return is_healthy
        except Exception as e:
            logger.error(f"[LLM] Health check failed with exception: {e}", exc_info=True)
            return False

    async def preload_model(self) -> bool:
        """Preload the model into memory.

        For llama-cpp-python, the model is already loaded in __init__,
        so this is a no-op that always returns True.

        Returns:
            True (model is already loaded)
        """
        logger.info("[LLM] Model already loaded in memory (llama-cpp-python)")
        return True

    def _get_provider_name(self) -> str:
        """Get provider name for prompt generation."""
        return "llamacpp"

    def _create_tools_legacy(self) -> list[Tool]:
        """Legacy tool creation method (now handled by parent class)."""
        return [
            # ============================================================
            # READ-ONLY TOOLS - Priority 1 (Have API Tests)
            # ============================================================
            Tool(
                name="search_contacts",
                description="Search for contacts by name, email, or other criteria. Pass empty string to get ALL contacts.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": 'Search term to find contacts. Use empty string "" to return all contacts.',
                        }
                    },
                    "required": [],
                },
                function=self.api.search_contacts,
            ),
            Tool(
                name="list_all_contacts",
                description="Get a complete list of all contacts in the database. Use this when user wants to see everyone, not search for specific contacts.",
                parameters={"type": "object", "properties": {}},
                function=self.api.list_all_contacts,
            ),
            Tool(
                name="list_all_tags",
                description="Get a complete list of all tags in the database. Shows tag names and how many contacts have each tag. Use this to see all available tags.",
                parameters={"type": "object", "properties": {}},
                function=self.api.list_all_tags,
            ),
            Tool(
                name="list_all_notes",
                description="Get a complete list of all notes in the database. Shows note titles, content, and how many contacts have each note. Use this to see all available notes.",
                parameters={"type": "object", "properties": {}},
                function=self.api.list_all_notes,
            ),
            Tool(
                name="get_database_stats",
                description="Get database statistics including total contact count and relationship count. Use this for quick overview questions like 'How many contacts do I have?'",
                parameters={"type": "object", "properties": {}},
                function=self.api.get_database_stats,
            ),
            Tool(
                name="get_contact_details",
                description="Get detailed information about a specific contact by ID. Returns full contact information including all relationships, tags, and notes.",
                parameters={
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "integer",
                            "description": "ID of the contact to get details for",
                        }
                    },
                    "required": ["contact_id"],
                },
                function=self.api.get_contact_details,
            ),
            Tool(
                name="search_tags",
                description="Search for tags by name. Returns matching tags with contact counts. Use when user wants to find tags matching a pattern.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search term to find tags"}
                    },
                    "required": ["query"],
                },
                function=self.api.search_tags,
            ),
            Tool(
                name="search_notes",
                description="Search for notes by title or content. Returns matching notes with contact counts. Use when user wants to find notes matching a pattern.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search term to find notes in titles or content",
                        }
                    },
                    "required": ["query"],
                },
                function=self.api.search_notes,
            ),
            Tool(
                name="get_contacts_by_tag",
                description="Get all contacts that have a specific tag. Use when user asks 'who is tagged as X' or 'show me all my X contacts'. Returns full contact details for each match.",
                parameters={
                    "type": "object",
                    "properties": {
                        "tag_name": {
                            "type": "string",
                            "description": "Exact name of the tag to search for",
                        }
                    },
                    "required": ["tag_name"],
                },
                function=self.api.get_contacts_by_tag,
            ),
            Tool(
                name="get_contacts_by_note",
                description="Get all contacts that have a specific note. Use when user asks 'who has the note X' or 'show contacts with note X'. Returns full contact details for each match.",
                parameters={
                    "type": "object",
                    "properties": {
                        "note_title": {
                            "type": "string",
                            "description": "Exact title of the note to search for",
                        }
                    },
                    "required": ["note_title"],
                },
                function=self.api.get_contacts_by_note,
            ),
        ]

    # ============================================================
    # ABSTRACT METHOD IMPLEMENTATIONS FOR BaseLLM
    # ============================================================

    def _send_message_with_tools(self, messages: list[dict], tools: list[Tool]) -> str:
        """Send message with tools to LlamaCpp model.

        Args:
            messages: Message history
            tools: Available tools

        Returns:
            Model response text
        """
        # Build conversation context
        conversation_text = ""
        system_prompt = ""

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            elif msg["role"] == "user":
                conversation_text += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                conversation_text += f"Assistant: {msg['content']}\n"
            elif msg["role"] == "tool":
                conversation_text += f"Tool Result: {msg['content']}\n"

        # Create prompt with tool guidance for LlamaCpp
        prompt = f"""{system_prompt}

{conversation_text}Assistant: """

        try:
            result = self.llm.create_completion(
                prompt=prompt,
                max_tokens=4000,  # Allow longer responses
                temperature=self.temperature,
                stop=["User:"],  # Stop at next user input
            )

            response_text = result["choices"][0]["text"].strip()
            logger.debug(f"[LLM] Generated response: {response_text[:200]}...")
            return response_text

        except Exception as e:
            logger.error(f"[LLM] Error in LlamaCpp completion: {e}")
            return f"Error generating response: {e}"

    def _extract_tool_calls(self, response: str) -> list[dict]:
        """Extract tool calls from LlamaCpp text response.

        Args:
            response: Text response from LlamaCpp

        Returns:
            List of tool call dictionaries
        """
        # Look for JSON tool calls in response
        try:
            # Extract JSON from code blocks or plain text
            import re

            json_pattern = r"```json\s*(\{.*?\})\s*```|(\{.*?\})"
            matches = re.findall(json_pattern, response, re.DOTALL)

            for match in matches:
                json_str = match[0] if match[0] else match[1]
                if not json_str:
                    continue

                parsed = json.loads(json_str)
                if "tool_calls" in parsed and isinstance(parsed["tool_calls"], list):
                    # Add IDs for compatibility
                    for i, tool_call in enumerate(parsed["tool_calls"]):
                        tool_call["id"] = f"call_{i}"
                    return parsed["tool_calls"]

        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"[LLM] No tool calls found in response: {e}")

        return []

    def _extract_assistant_message(self, response: str) -> str:
        """Extract assistant message from LlamaCpp response.

        Args:
            response: LlamaCpp response text

        Returns:
            Assistant message text
        """
        # Remove any JSON tool calls from the response for user display
        import re

        # Remove JSON code blocks
        clean_response = re.sub(r"```json.*?```", "", response, flags=re.DOTALL)

        # Remove standalone JSON objects
        clean_response = re.sub(r'\{[^}]*"tool_calls"[^}]*\}', "", clean_response)

        return clean_response.strip()

    # ============================================================
    # LEGACY METHODS (to be removed after testing)
    # ============================================================

    def _get_tool_by_name(self, name: str) -> Tool | None:
        """Get a tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def _call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool with the given arguments."""
        tool = self._get_tool_by_name(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            # Special handling for search_contacts
            if tool_name == "search_contacts":
                if "query" not in arguments:
                    arguments["query"] = ""
                else:
                    query = str(arguments["query"]).strip()
                    query = query.strip("?!.,;:'\"")
                    arguments["query"] = query

            # Filter arguments to only include parameters defined in tool schema
            if tool.parameters and "properties" in tool.parameters:
                allowed_params = set(tool.parameters["properties"].keys())
                filtered_args = {k: v for k, v in arguments.items() if k in allowed_params}
                logger.debug(
                    f"[LLM] Filtered arguments from {list(arguments.keys())} "
                    f"to {list(filtered_args.keys())}"
                )
                arguments = filtered_args

            result = tool.function(**arguments)
            return result
        except Exception as e:
            return {"error": f"Error calling tool '{tool_name}': {str(e)}"}

    def _create_system_prompt(self, schema_detail: str = "essential") -> str:
        """Create the system prompt for the LLM.

        Args:
            schema_detail: "essential" for concise prompt, "detailed" for full prompt
        """
        tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
        tool_count = len(self.tools)

        return f"""You are an AI assistant for the Personal Relationship Toolkit (PRT), a privacy-first personal contact management system.

## ABOUT PRT

PRT is a LOCAL-ONLY tool designed to help users:
1. **Store contact data privately** - No cloud sync, no corporate surveillance, all data stays on the user's device
2. **Remember faces and names** - Visual directories help with memorization
3. **Find people quickly** - Multi-faceted search with your assistance
4. **Build stronger relationships** - Track tags, notes, and connections

**Vision**: Create a "safe space" to discover and enhance relationships. This is the user's private database for their personal network.

## YOUR ROLE

You are the natural language interface to PRT running in a **Text User Interface (TUI)** - a terminal application with visual widgets and screens.

Key responsibilities:
- Help users search, view, and understand their contact data
- Answer questions about their relationships, tags, and notes
- Suggest helpful visualizations when appropriate (but never auto-generate)
- Provide a conversational, helpful interface to their private data

## USER INTERFACE CONTEXT

You are presenting information in a TUI (Text User Interface):
- **Chat messages appear in a scrollable widget** with user messages on the right, your responses on the left
- **Keep responses concise** - users can't easily scroll during long responses
- **Use markdown** for formatting: **bold**, *italic*, `code`, lists, etc.
- **The TUI has dedicated screens** for viewing contacts, managing tags/notes, etc. - you complement those screens

## AVAILABLE TOOLS ({tool_count} total, all read-only)

{tools_description}

## TOOL CALLING FORMAT

When you need to use a tool, respond with a JSON object in this EXACT format:
```json
{{
  "tool_calls": [
    {{
      "name": "tool_name",
      "arguments": {{
        "param1": "value1",
        "param2": "value2"
      }}
    }}
  ]
}}
```

After receiving tool results, provide a natural language response to the user based on the data.

## USAGE INSTRUCTIONS

1. **Search First**: When users ask about contacts/tags/notes, use appropriate search/list tools to get real data
2. **Be Specific**: Use exact tool names and required parameters
3. **Never Make Up Data**: Always use tools to get information from the database
4. **Directory Generation**:
   - When showing many contacts (>10), you MAY offer to generate an interactive directory visualization
   - NEVER auto-generate directories - only create them if the user explicitly requests
5. **Error Handling**: If a tool fails, explain the error clearly and suggest alternatives
6. **Result Limits**: If query returns many results (>50), summarize and offer to narrow the search

## RESPONSE STYLE

- **Friendly and conversational**: "I found 15 contacts tagged as 'family'! Would you like to see them all or search more specifically?"
- **Concise but complete**: Provide key info without overwhelming the TUI
- **Proactive**: Suggest next steps: "I can also show you all tags if that helps"
- **Privacy-aware**: Remind users their data is private and local when relevant
- **Humble**: If you don't know something, say so - don't guess about PRT features

## LIMITATIONS

- You cannot modify data (write operations disabled in current phase)
- You cannot access files outside the PRT database
- You cannot run system commands or modify configuration
- You cannot access the internet or external services
- You cannot generate directories without explicit user request

Remember: PRT is a "safe space" for relationship data. Be helpful, be safe, respect privacy, and never presume to create visualizations without permission."""

    def _format_messages_for_llama(self, messages: list[dict[str, Any]]) -> str:
        """Format conversation messages into a prompt for llama.cpp.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Formatted prompt string for llama.cpp
        """
        # Llama 3 uses a specific chat template format
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                prompt += f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "user":
                prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "assistant":
                prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "tool":
                # Format tool results as assistant observations
                prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\nTool result: {content}<|eot_id|>"

        # Add assistant header for the next response
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return prompt

    def _parse_tool_calls(self, response: str) -> list[dict[str, Any]] | None:
        """Parse tool calls from model response.

        Args:
            response: Raw model response text

        Returns:
            List of tool call dictionaries, or None if no valid tool calls found
        """
        try:
            # Try to find JSON object in response
            # Look for ```json or just a JSON object
            import re

            json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
            if not json_match:
                json_match = re.search(r"(\{.*?\})", response, re.DOTALL)

            if not json_match:
                return None

            json_str = json_match.group(1)
            parsed = json.loads(json_str)

            if "tool_calls" in parsed and isinstance(parsed["tool_calls"], list):
                return parsed["tool_calls"]

            return None
        except (json.JSONDecodeError, AttributeError) as e:
            logger.debug(f"[LLM] Failed to parse tool calls: {e}")
            return None

    def chat(self, message: str) -> str:
        """Send a message to the LLM and get a response."""
        logger.info(f"[LLM] Starting chat with message: {message[:100]}...")

        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        # Prepare messages with system prompt
        messages = [
            {"role": "system", "content": self._create_system_prompt()}
        ] + self.conversation_history

        # Format messages for llama.cpp
        prompt = self._format_messages_for_llama(messages)

        logger.debug(f"[LLM] Formatted prompt length: {len(prompt)} chars")

        try:
            # Generate completion
            logger.debug("[LLM] Calling llama.cpp completion...")
            response = self.llm.create_completion(
                prompt=prompt,
                max_tokens=1024,
                temperature=self.temperature,
                stop=["<|eot_id|>", "<|end_of_text|>"],
            )

            if not response or "choices" not in response or not response["choices"]:
                logger.error("[LLM] Invalid response from llama.cpp")
                return "Error: Invalid response from model"

            assistant_message = response["choices"][0]["text"].strip()
            logger.debug(f"[LLM] Raw response: {assistant_message[:200]}...")

            # Check if response contains tool calls
            tool_calls = self._parse_tool_calls(assistant_message)

            if tool_calls:
                logger.info(f"[LLM] Found {len(tool_calls)} tool calls")
                tool_results = []

                for tool_call in tool_calls:
                    tool_name = tool_call.get("name", "")
                    arguments = tool_call.get("arguments", {})

                    if not tool_name:
                        logger.warning("[LLM] Tool call missing name field")
                        continue

                    logger.info(f"[LLM] Executing tool: {tool_name}")
                    tool_result = self._call_tool(tool_name, arguments)
                    logger.debug(f"[LLM] Tool {tool_name} result: {str(tool_result)[:200]}")

                    tool_results.append({"name": tool_name, "result": tool_result})

                # Add assistant message with tool calls to history
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )

                # Add tool results to history
                for tool_result in tool_results:
                    self.conversation_history.append(
                        {
                            "role": "tool",
                            "content": json.dumps(
                                tool_result["result"], default=self._json_serializer
                            ),
                        }
                    )

                # Get final response after tool execution
                logger.info(f"[LLM] Requesting final response after {len(tool_results)} tool calls")

                # Format messages again with tool results
                final_messages = [
                    {"role": "system", "content": self._create_system_prompt()}
                ] + self.conversation_history
                final_prompt = self._format_messages_for_llama(final_messages)

                final_response = self.llm.create_completion(
                    prompt=final_prompt,
                    max_tokens=1024,
                    temperature=self.temperature,
                    stop=["<|eot_id|>", "<|end_of_text|>"],
                )

                if not final_response or "choices" not in final_response:
                    logger.error("[LLM] Invalid final response")
                    return "Error: Invalid final response from model"

                final_message = final_response["choices"][0]["text"].strip()
                logger.info(f"[LLM] Final response: {final_message[:100]}...")

                # Add final assistant message to history
                self.conversation_history.append({"role": "assistant", "content": final_message})

                return final_message
            else:
                # No tool calls, just return the response
                logger.info(f"[LLM] Direct response (no tools): {assistant_message[:100]}...")
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )
                return assistant_message

        except Exception as e:
            logger.error(f"[LLM] Error during chat: {e}", exc_info=True)
            return f"Error processing request: {str(e)}"

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("[LLM] Conversation history cleared")

    def _json_serializer(self, obj):
        """Custom JSON serializer to handle non-serializable objects like bytes.

        Args:
            obj: Object to serialize

        Returns:
            Serializable representation of the object
        """
        if isinstance(obj, bytes):
            return f"<binary data: {len(obj)} bytes>"
        elif hasattr(obj, "__dict__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        else:
            return str(obj)
