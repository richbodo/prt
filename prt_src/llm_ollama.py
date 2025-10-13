"""
Ollama LLM Integration for PRT

This module provides integration with Ollama for running GPT-OSS-20B locally
with tool calling capabilities for PRT operations.
"""

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

import requests

from .api import PRTAPI
from .config import LLMConfigManager
from .logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Tool:
    """Represents a tool that can be called by the LLM."""

    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable


class OllamaLLM:
    """Ollama LLM client with tool calling support."""

    def __init__(
        self,
        api: PRTAPI,
        base_url: Optional[str] = None,
        keep_alive: Optional[str] = None,
        timeout: Optional[int] = None,
        config_manager: Optional[LLMConfigManager] = None,
    ):
        """Initialize Ollama LLM client.

        Args:
            api: PRTAPI instance for database operations
            base_url: Ollama API base URL (deprecated, use config_manager)
            keep_alive: How long to keep model loaded in memory (deprecated, use config_manager)
            timeout: Request timeout in seconds (deprecated, use config_manager)
            config_manager: LLMConfigManager instance. If None, loads config automatically.

        Note:
            The base_url, keep_alive, and timeout parameters are deprecated in favor of
            config_manager. They are kept for backward compatibility but will be removed
            in a future version.
        """
        self.api = api

        # Load configuration
        if config_manager is None:
            config_manager = LLMConfigManager()
        self.config_manager = config_manager

        # Use config values, falling back to explicit parameters (backward compat)
        self.base_url = base_url if base_url is not None else config_manager.llm.base_url
        self.model = config_manager.llm.model
        self.keep_alive = keep_alive if keep_alive is not None else config_manager.llm.keep_alive
        self.timeout = timeout if timeout is not None else config_manager.llm.timeout
        self.temperature = config_manager.llm.temperature

        self.tools = self._create_tools()
        self.conversation_history = []

        logger.info(
            f"[LLM] Initialized OllamaLLM: model={self.model}, keep_alive={self.keep_alive}, timeout={self.timeout}s"
        )

    async def health_check(self, timeout: float = 2.0) -> bool:
        """Quick health check to see if Ollama is responsive.

        Args:
            timeout: Timeout in seconds for the health check

        Returns:
            True if Ollama is available and responsive, False otherwise
        """
        try:
            # Run the synchronous request in a thread pool to avoid blocking the event loop
            response = await asyncio.to_thread(
                requests.get, f"{self.base_url.replace('/v1', '')}/api/tags", timeout=timeout
            )
            return response.status_code == 200
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            return False
        except Exception:
            return False

    async def preload_model(self) -> bool:
        """Preload the model into memory to avoid cold start delays.

        Why preloading is necessary:
        - The gpt-oss:20b model is 13GB and takes 20-40 seconds to load from disk
        - Ollama unloads models after 5 minutes of inactivity by default
        - Without preloading, the first chat request after idle time must:
          1. Load the 13GB model (20-40 seconds)
          2. Process the request (10-80+ seconds depending on complexity)
          Total: Can exceed 120 second timeout, causing failures
        - Preloading on screen mount ensures the model is ready before user sends messages
        - The keep_alive setting (default 30m) keeps model loaded between requests

        Performance impact:
        - Short queries work without preload (~10-20s total including load time)
        - Large generation requests (100+ lines) require preload to avoid timeout
        - Preload adds 20-30s to chat screen startup but eliminates timeout risk

        Returns:
            True if model was successfully loaded, False otherwise
        """
        try:
            logger.info(f"[LLM] Preloading model {self.model} into memory...")

            # Use Ollama's generate endpoint with empty prompt to load the model
            # This keeps the model in memory according to keep_alive setting
            response = await asyncio.to_thread(
                requests.post,
                f"{self.base_url.replace('/v1', '')}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "",
                    "keep_alive": self.keep_alive,
                },
                timeout=30,
            )

            if response.status_code == 200:
                logger.info(f"[LLM] Model {self.model} preloaded successfully")
                return True
            else:
                logger.warning(f"[LLM] Model preload returned status {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"[LLM] Failed to preload model: {e}")
            return False

    def _create_tools(self) -> List[Tool]:
        """Create the available tools for the LLM.

        PHASE 1: Starting with just search_contacts to prove the concept.
        Other tools are commented out until we validate this approach works.
        """
        return [
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
                    "required": [],  # query is optional - defaults to empty string
                },
                function=self.api.search_contacts,
            ),
            # PHASE 2: Add these tools after search_contacts is proven reliable
            # Tool(
            #     name="list_all_contacts",
            #     description="Get a list of all contacts in the database",
            #     parameters={"type": "object", "properties": {}},
            #     function=self.api.list_all_contacts,
            # ),
            # Tool(
            #     name="get_contact_details",
            #     description="Get detailed information about a specific contact",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "contact_id": {
            #                 "type": "integer",
            #                 "description": "ID of the contact to get details for",
            #             }
            #         },
            #         "required": ["contact_id"],
            #     },
            #     function=self.api.get_contact_details,
            # ),
            # Tool(
            #     name="search_tags",
            #     description="Search for tags by name",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "query": {"type": "string", "description": "Search term to find tags"}
            #         },
            #         "required": ["query"],
            #     },
            #     function=self.api.search_tags,
            # ),
            # Tool(
            #     name="list_all_tags",
            #     description="Get a list of all tags in the database",
            #     parameters={"type": "object", "properties": {}},
            #     function=self.api.list_all_tags,
            # ),
            # Tool(
            #     name="get_contacts_by_tag",
            #     description="Get all contacts that have a specific tag",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "tag_name": {
            #                 "type": "string",
            #                 "description": "Name of the tag to search for",
            #             }
            #         },
            #         "required": ["tag_name"],
            #     },
            #     function=self.api.get_contacts_by_tag,
            # ),
            # Tool(
            #     name="search_notes",
            #     description="Search for notes by title or content",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "query": {"type": "string", "description": "Search term to find notes"}
            #         },
            #         "required": ["query"],
            #     },
            #     function=self.api.search_notes,
            # ),
            # Tool(
            #     name="list_all_notes",
            #     description="Get a list of all notes in the database",
            #     parameters={"type": "object", "properties": {}},
            #     function=self.api.list_all_notes,
            # ),
            # Tool(
            #     name="get_contacts_by_note",
            #     description="Get all contacts that have a specific note",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "note_title": {
            #                 "type": "string",
            #                 "description": "Title of the note to search for",
            #             }
            #         },
            #         "required": ["note_title"],
            #     },
            #     function=self.api.get_contacts_by_note,
            # ),
            # Tool(
            #     name="add_tag_to_contact",
            #     description="Add a tag to a contact's relationship",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "contact_id": {"type": "integer", "description": "ID of the contact"},
            #             "tag_name": {"type": "string", "description": "Name of the tag to add"},
            #         },
            #         "required": ["contact_id", "tag_name"],
            #     },
            #     function=self.api.add_tag_to_contact,
            # ),
            # Tool(
            #     name="add_note_to_contact",
            #     description="Add a note to a contact's relationship",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "contact_id": {"type": "integer", "description": "ID of the contact"},
            #             "note_title": {"type": "string", "description": "Title of the note"},
            #             "note_content": {"type": "string", "description": "Content of the note"},
            #         },
            #         "required": ["contact_id", "note_title", "note_content"],
            #     },
            #     function=self.api.add_note_to_contact,
            # ),
            # Tool(
            #     name="create_tag",
            #     description="Create a new tag",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "name": {"type": "string", "description": "Name of the tag to create"}
            #         },
            #         "required": ["name"],
            #     },
            #     function=self.api.create_tag,
            # ),
            # Tool(
            #     name="create_note",
            #     description="Create a new note",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "title": {"type": "string", "description": "Title of the note"},
            #             "content": {"type": "string", "description": "Content of the note"},
            #         },
            #         "required": ["title", "content"],
            #     },
            #     function=self.api.create_note,
            # ),
            # Tool(
            #     name="get_database_stats",
            #     description="Get database statistics including contact and relationship counts",
            #     parameters={"type": "object", "properties": {}},
            #     function=self.api.get_database_stats,
            # ),
            # Tool(
            #     name="create_backup_with_comment",
            #     description="Create a manual database backup with an optional comment",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "comment": {
            #                 "type": "string",
            #                 "description": "Optional description for the backup",
            #             }
            #         },
            #     },
            #     function=self.api.create_backup_with_comment,
            # ),
            # Tool(
            #     name="execute_sql",
            #     description="Execute a raw SQL query. Write operations require confirm=true and trigger an automatic backup",
            #     parameters={
            #         "type": "object",
            #         "properties": {
            #             "sql": {
            #                 "type": "string",
            #                 "description": "SQL to execute",
            #             },
            #             "confirm": {
            #                 "type": "boolean",
            #                 "description": "Must be true for write operations",
            #             },
            #         },
            #         "required": ["sql"],
            #     },
            #     function=self.api.execute_sql,
            # ),
        ]

    def _get_tool_by_name(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool with the given arguments."""
        tool = self._get_tool_by_name(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}

        try:
            # Special handling for search_contacts: clean and default query parameter
            if tool_name == "search_contacts":
                if "query" not in arguments:
                    arguments["query"] = ""
                else:
                    # Clean the query: remove trailing punctuation, quotes, whitespace
                    query = str(arguments["query"]).strip()
                    # Remove common punctuation that's not part of search terms
                    query = query.strip("?!.,;:'\"")
                    # If empty after cleaning, use empty string (searches all)
                    arguments["query"] = query

            result = tool.function(**arguments)
            return result
        except Exception as e:
            return {"error": f"Error calling tool '{tool_name}': {str(e)}"}

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the LLM."""
        tools_description = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])

        return f"""You are an AI assistant for the Personal Relationship Toolkit (PRT), a private contact and relationship management system.

Your role is to help users manage their personal contacts, relationships, tags, and notes. You have access to a private database containing the user's contact information.

CONTEXT:
- This is a personal relationship management tool
- All data is stored locally in a private database
- You can search, view, and manage contacts, tags, and notes
- You should be helpful, conversational, and respect privacy

AVAILABLE TOOLS:
{tools_description}

INSTRUCTIONS:
 1. When a user asks about their contacts, relationships, tags, or notes, use the appropriate tools to get real data
 2. Always use tools to perform actions rather than making up information
 3. If a user asks a general question about PRT or how to use it, respond directly without using tools
 4. Be concise but helpful in your responses
 5. If a tool call fails, explain the issue and suggest alternatives
 6. For complex requests, break them down into multiple tool calls if needed
 7. Direct SQL queries via execute_sql require caution: write operations need confirm=true and will trigger an automatic backup

EXAMPLES:
- "Show me all contacts" → Use list_all_contacts tool
- "Find contacts named John" → Use search_contacts tool with query="John"
- "What is PRT?" → Respond directly (no tool needed)
- "How do I add a tag?" → Respond directly with instructions

Remember: You can only use the tools listed above. You cannot access files, run commands, or modify system configuration."""

    def _format_tool_calls(self) -> List[Dict[str, Any]]:
        """Format tools for Ollama API."""
        return [
            {"name": tool.name, "description": tool.description, "parameters": tool.parameters}
            for tool in self.tools
        ]

    def chat(self, message: str) -> str:
        """Send a message to the LLM and get a response."""
        logger.info(f"[LLM] Starting chat with message: {message[:100]}...")

        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        # Prepare the request for Ollama
        request_data = {
            "model": self.model,
            "messages": [{"role": "system", "content": self._create_system_prompt()}]
            + self.conversation_history,
            "tools": self._format_tool_calls(),
            "stream": False,
            "keep_alive": self.keep_alive,
        }

        url = f"{self.base_url}/chat/completions"
        logger.info(f"[LLM] Sending request to {url}, model={self.model}, timeout={self.timeout}s")
        logger.debug(f"[LLM] Message history length: {len(self.conversation_history)}")

        try:
            # Send request to Ollama
            logger.debug("[LLM] Making POST request to Ollama...")
            response = requests.post(
                url,
                json=request_data,
                timeout=self.timeout,
            )
            logger.debug(f"[LLM] Received response with status code: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            logger.debug(
                f"[LLM] Received JSON response with {len(result.get('choices', []))} choices"
            )

            # Validate response structure
            if not result.get("choices") or not result["choices"]:
                logger.error("[LLM] Invalid response: no choices found")
                return "Error: Invalid response from Ollama - no choices found"

            choice = result["choices"][0]
            if not choice.get("message"):
                logger.error("[LLM] Invalid response: no message in choice")
                return "Error: Invalid response from Ollama - no message found"

            message_obj = choice["message"]
            logger.debug(f"[LLM] Message object keys: {list(message_obj.keys())}")

            # Check if the LLM wants to call a tool
            if "tool_calls" in message_obj and message_obj["tool_calls"]:
                tool_calls = message_obj["tool_calls"]
                logger.info(f"[LLM] LLM requested {len(tool_calls)} tool calls")
                tool_results = []

                # Limit to prevent infinite loops
                if len(tool_calls) > 5:
                    logger.warning(f"[LLM] Too many tool calls requested: {len(tool_calls)}")
                    return "Error: Too many tool calls requested. Please try a simpler query."

                for tool_call in tool_calls:
                    if not tool_call.get("function"):
                        continue

                    tool_name = tool_call["function"]["name"]
                    arguments_str = tool_call["function"].get("arguments", "{}")
                    logger.info(f"[LLM] Executing tool: {tool_name}")

                    # Parse arguments if it's a string
                    try:
                        arguments = (
                            json.loads(arguments_str)
                            if isinstance(arguments_str, str)
                            else arguments_str
                        )
                        logger.debug(f"[LLM] Tool arguments: {arguments}")
                    except json.JSONDecodeError as e:
                        logger.error(f"[LLM] Failed to parse tool arguments: {e}")
                        arguments = {}

                    # Call the tool
                    tool_result = self._call_tool(tool_name, arguments)
                    logger.debug(f"[LLM] Tool {tool_name} result: {str(tool_result)[:200]}")
                    tool_results.append(
                        {
                            "tool_call_id": tool_call.get("id", ""),
                            "name": tool_name,
                            "result": tool_result,
                        }
                    )

                # Add assistant message with tool calls to history
                self.conversation_history.append(message_obj)

                # Add tool results to history
                for tool_result in tool_results:
                    self.conversation_history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_result["tool_call_id"],
                            "content": json.dumps(
                                tool_result["result"], default=self._json_serializer
                            ),
                        }
                    )

                # Get final response from LLM
                logger.info("[LLM] Requesting final response after tool calls")
                final_request = {
                    "model": self.model,
                    "messages": [{"role": "system", "content": self._create_system_prompt()}]
                    + self.conversation_history,
                    "stream": False,
                    "keep_alive": self.keep_alive,
                }

                final_response = requests.post(
                    f"{self.base_url}/chat/completions",
                    json=final_request,
                    timeout=self.timeout,
                )
                logger.debug(f"[LLM] Final response status: {final_response.status_code}")
                final_response.raise_for_status()

                final_result = final_response.json()

                if not final_result.get("choices") or not final_result["choices"]:
                    logger.error("[LLM] Invalid final response: no choices")
                    return "Error: Invalid final response from Ollama"

                assistant_message = final_result["choices"][0]["message"]["content"]
                logger.info(f"[LLM] Final response received: {assistant_message[:100]}...")

                # Add final assistant message to history
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )

                return assistant_message
            else:
                # No tool calls, just return the response
                assistant_message = message_obj["content"]
                logger.info(f"[LLM] Direct response (no tools): {assistant_message[:100]}...")
                self.conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )
                return assistant_message

        except requests.exceptions.Timeout as e:
            logger.error(f"[LLM] Request timed out after {self.timeout}s: {e}")
            return f"Error: Request to Ollama timed out after {self.timeout} seconds. The model may need more time to load or process this request."
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[LLM] Connection error: {e}")
            return "Error: Cannot connect to Ollama. Please make sure Ollama is running on localhost:11434"
        except requests.exceptions.RequestException as e:
            logger.error(f"[LLM] Request exception: {e}", exc_info=True)
            return f"Error communicating with Ollama: {str(e)}"
        except Exception as e:
            logger.error(f"[LLM] Unexpected error: {e}", exc_info=True)
            return f"Error processing response: {str(e)}"

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []

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
            # For objects with attributes, return a dict representation (excluding private attrs)
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        else:
            return str(obj)


def chat_with_ollama(api: PRTAPI, message: str = None) -> str:
    """Convenience function to chat with Ollama LLM."""
    llm = OllamaLLM(api)

    if message:
        return llm.chat(message)
    else:
        return "Ollama LLM initialized. You can now chat with me about your contacts and relationships!"


def start_ollama_chat(api: PRTAPI):
    """Start an interactive chat session with Ollama."""
    from rich.console import Console
    from rich.prompt import Prompt

    console = Console()
    llm = OllamaLLM(api)

    console.print("🤖 Ollama LLM Chat Mode", style="bold blue")
    console.print(
        "Type 'quit' to exit, 'clear' to clear history, 'help' for assistance", style="cyan"
    )
    console.print("=" * 50, style="blue")

    # Test connection first
    console.print("Testing connection to Ollama...", style="yellow")
    try:
        test_response = requests.get(f"{llm.base_url}/models", timeout=5)
        if test_response.status_code == 200:
            console.print("✓ Connected to Ollama", style="green")
        else:
            console.print("⚠ Warning: Ollama connection test failed", style="yellow")
    except Exception as e:
        console.print(f"⚠ Warning: Cannot connect to Ollama: {e}", style="yellow")
        console.print("Make sure Ollama is running with: ollama serve", style="cyan")

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")

            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("Goodbye!", style="green")
                break
            elif user_input.lower() == "clear":
                llm.clear_history()
                console.print("Chat history cleared.", style="yellow")
                continue
            elif user_input.lower() == "help":
                console.print("\n[bold blue]Available Commands:[/bold blue]")
                console.print("- Type your questions about contacts, tags, or notes", style="white")
                console.print("- 'clear': Clear chat history", style="white")
                console.print("- 'quit' or 'exit': Exit chat mode", style="white")
                console.print("\n[bold blue]Example Questions:[/bold blue]")
                console.print("- 'Show me all contacts'", style="white")
                console.print("- 'Find contacts named John'", style="white")
                console.print("- 'What tags do I have?'", style="white")
                console.print("- 'How many contacts do I have?'", style="white")
                continue
            elif not user_input.strip():
                continue

            console.print("\n[bold blue]Assistant[/bold blue]")
            console.print("Thinking...", style="dim")
            response = llm.chat(user_input)
            console.print(response, style="white")

        except (KeyboardInterrupt, EOFError):
            console.print("\nGoodbye!", style="green")
            break
        except Exception as e:
            console.print(f"Error: {e}", style="red")
            console.print(
                "Try asking a simpler question or type 'help' for assistance.", style="yellow"
            )
