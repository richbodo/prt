"""High-fidelity mock of OllamaLLM for fast, deterministic testing."""

import json
import re
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from prt_src.api import PRTAPI
from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class ResponsePatterns:
    """Pre-defined response patterns for common queries."""

    PATTERNS = {
        r"how many contacts": "You have {contact_count} contacts in your database.",
        r"list.*contacts": "Here are your contacts: {contact_list}",
        r"search.*john": "Found {john_count} contacts matching 'John'",
        r"search.*contacts.*(.+)": "Found {search_count} contacts matching '{search_term}'",
        r"create.*directory": "Directory created successfully at {output_path}",
        r"database.*stats": "Database contains {contact_count} contacts, {tag_count} tags, and {note_count} notes.",
        r"get.*contact.*by.*id.*(\d+)": "Contact details for ID {contact_id}: {contact_info}",
        r"add.*tag.*(.+)": "Added tag '{tag_name}' successfully.",
        r"add.*note.*(.+)": "Added note '{note_title}' successfully.",
        r"export.*contacts": "Exported {export_count} contacts to {export_path}",
        r"help|what.*can.*do": "I can help you manage contacts, search your database, create directories, and more. Available tools: get_database_stats, search_contacts, get_contact_by_id, add_tag, add_note, export_contacts.",
        r"test.*tool.*calling": "Tool calling is working correctly. Available tools: {tool_list}",
        r"(get|show|find|list).*contacts.*(image|photo|picture)": "Found {contacts_with_images_count} contacts with profile images: {contacts_with_images_list}",
        r"create.*directory.*(image|photo|picture)": "I'll create a directory of contacts with images. Let me gather the contacts and generate the directory... Created directory with {contacts_with_images_count} contacts at {directory_path}",
        r"contacts.*(with|have).*(image|photo|picture)": "You have {contacts_with_images_count} contacts with profile images in your database.",
        r".*": "I understand you're asking about: {query}. I can help with contact management, search, and database operations.",  # Fallback
    }


class MockOllamaLLM:
    """High-fidelity mock of OllamaLLM for fast, deterministic testing."""

    def __init__(self, api: PRTAPI, **kwargs):
        """Initialize mock LLM with API reference and tools."""
        self.api = api
        self.conversation_history = []
        self.tools = self._create_tools()
        self.response_overrides = {}
        self.last_tool_called = None
        self.tool_call_history = []

        # Model configuration (matching real LLM interface)
        self.model = kwargs.get("model", "mock-gpt-oss:20b")
        self.base_url = kwargs.get("base_url", "http://localhost:11434")
        self.timeout = kwargs.get("timeout", 30.0)

        logger.info(f"Initialized MockOllamaLLM with model: {self.model}")

    def _create_tools(self) -> List[Dict[str, Any]]:
        """Create tool definitions matching real LLM tools."""
        return [
            {
                "name": "get_database_stats",
                "description": "Get statistics about the database",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "search_contacts",
                "description": "Search for contacts by name, email, or other criteria",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Search query"}},
                    "required": ["query"],
                },
            },
            {
                "name": "get_contact_by_id",
                "description": "Get detailed information about a specific contact",
                "parameters": {
                    "type": "object",
                    "properties": {"contact_id": {"type": "integer", "description": "Contact ID"}},
                    "required": ["contact_id"],
                },
            },
            {
                "name": "add_tag",
                "description": "Add a new tag to the database",
                "parameters": {
                    "type": "object",
                    "properties": {"name": {"type": "string", "description": "Tag name"}},
                    "required": ["name"],
                },
            },
            {
                "name": "add_note",
                "description": "Add a new note to the database",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Note title"},
                        "content": {"type": "string", "description": "Note content"},
                    },
                    "required": ["title", "content"],
                },
            },
            {
                "name": "export_contacts",
                "description": "Export contacts to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "format": {"type": "string", "description": "Export format"},
                        "output_path": {"type": "string", "description": "Output file path"},
                    },
                    "required": ["format"],
                },
            },
        ]

    def set_response(self, query_pattern: str, response: str):
        """Inject specific response for testing scenarios."""
        self.response_overrides[query_pattern] = response
        logger.debug(f"Set response override for pattern: {query_pattern}")

    def _simulate_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Simulate tool execution with realistic responses."""
        self.last_tool_called = tool_name
        self.tool_call_history.append({"tool": tool_name, "args": arguments})

        logger.debug(f"Simulating tool call: {tool_name} with args: {arguments}")

        try:
            if tool_name == "get_database_stats":
                contacts = self.api.list_all_contacts()
                # Mock realistic stats
                return {
                    "contacts": len(contacts),
                    "tags": 8,  # From test fixtures
                    "notes": 6,  # From test fixtures
                    "relationships": 7,
                }

            elif tool_name == "search_contacts":
                query = arguments.get("query", "")
                # Use the real API to search for contacts
                matching_contacts = self.api.search_contacts(query)

                # If no real matches, check if query contains "john" and return mock data
                if not matching_contacts and "john" in query.lower():
                    return [{"id": 1, "name": "John Doe", "email": "john.doe@example.com"}]

                return matching_contacts[:5]  # Limit results

            elif tool_name == "get_contact_by_id":
                contact_id = arguments.get("contact_id")
                # Mock contact details
                return {
                    "id": contact_id,
                    "name": f"Contact {contact_id}",
                    "email": f"contact{contact_id}@example.com",
                    "phone": f"+1-555-{contact_id:04d}",
                }

            elif tool_name == "add_tag":
                tag_name = arguments.get("name")
                return {"success": True, "tag_id": 99, "name": tag_name}

            elif tool_name == "add_note":
                title = arguments.get("title")
                # content = arguments.get("content")  # Not used in mock response
                return {"success": True, "note_id": 99, "title": title}

            elif tool_name == "export_contacts":
                format_type = arguments.get("format", "json")
                output_path = arguments.get("output_path", f"/tmp/contacts.{format_type}")
                return {
                    "success": True,
                    "exported_count": 6,  # From test fixtures
                    "output_path": output_path,
                }

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.warning(f"Error in tool simulation: {e}")
            return {"error": str(e)}

    def _match_response_pattern(self, message: str) -> Optional[str]:
        """Match message against response patterns and return formatted response."""
        message_lower = message.lower()

        # Check for custom overrides first
        for pattern, response in self.response_overrides.items():
            if re.search(pattern.lower(), message_lower):
                return response

        # Check built-in patterns
        for pattern, template in ResponsePatterns.PATTERNS.items():
            match = re.search(pattern.lower(), message_lower)
            if match:
                # Extract any capture groups
                groups = match.groups() if match else ()

                # Get context data for template formatting
                context = self._get_response_context(message, groups)

                try:
                    return template.format(**context)
                except KeyError as e:
                    logger.warning(f"Template formatting error: {e}")
                    return template  # Return unformatted if formatting fails

        # Fallback response
        return f"I understand you're asking about: {message}. I can help with contact management, search, and database operations."

    def _get_response_context(self, message: str, groups: tuple) -> dict:
        """Get context data for response template formatting."""
        context = {}

        try:
            # Basic database stats
            contacts = self.api.list_all_contacts()
            contacts_with_images = self.api.get_contacts_with_images()

            context.update(
                {
                    "contact_count": len(contacts),
                    "tag_count": 8,  # From fixtures
                    "note_count": 6,  # From fixtures
                    "contact_list": ", ".join([c.get("name", "Unknown") for c in contacts[:3]]),
                    "tool_list": ", ".join([tool["name"] for tool in self.tools]),
                    "query": message,
                    "contacts_with_images_count": len(contacts_with_images),
                    "contacts_with_images_list": ", ".join(
                        [c.get("name", "Unknown") for c in contacts_with_images[:3]]
                    ),
                    "directory_path": "/mock/directories/contacts_with_images",
                }
            )

            # Handle specific patterns with groups
            if groups and len(groups) >= 1:
                search_term = groups[0]
                context.update(
                    {
                        "search_term": search_term,
                        "search_count": 2,  # Mock search result count
                        "john_count": 2,  # Mock John search count
                        "contact_id": groups[0] if groups[0].isdigit() else "1",
                        "tag_name": groups[0],
                        "note_title": groups[0],
                        "export_count": len(contacts),
                        "export_path": "/tmp/contacts_export.json",
                        "output_path": "/tmp/directory.html",
                    }
                )

                # Mock contact info for specific ID
                if groups[0].isdigit():
                    contact_id = int(groups[0])
                    context["contact_info"] = (
                        f"Name: Contact {contact_id}, Email: contact{contact_id}@example.com"
                    )

        except Exception as e:
            logger.warning(f"Error getting response context: {e}")
            # Provide safe defaults
            context.update(
                {
                    "contact_count": 0,
                    "tag_count": 0,
                    "note_count": 0,
                    "contact_list": "",
                    "tool_list": "get_database_stats, search_contacts",
                    "query": message,
                }
            )

        return context

    def _should_call_tool(self, message: str) -> Optional[tuple]:
        """Determine if message should trigger a tool call."""
        message_lower = message.lower()

        # Tool calling patterns
        if any(phrase in message_lower for phrase in ["how many", "count", "stats", "database"]):
            return ("get_database_stats", {})
        elif (
            "create" in message_lower
            and "directory" in message_lower
            and any(img_word in message_lower for img_word in ["image", "photo", "picture"])
        ):
            # Extract output name if provided
            output_name = None
            if "called" in message_lower or "named" in message_lower:
                words = message.split()
                for i, word in enumerate(words):
                    if word.lower() in ["called", "named"] and i + 1 < len(words):
                        output_name = words[i + 1].strip(".,!?\"'")
                        break
            return ("_create_directory_from_contacts_with_images", {"output_name": output_name})
        elif (
            any(phrase in message_lower for phrase in ["get", "show", "find", "list"])
            and "contact" in message_lower
            and any(img_word in message_lower for img_word in ["image", "photo", "picture"])
        ):
            return ("_get_contacts_with_images", {})
        elif (
            any(phrase in message_lower for phrase in ["search", "find", "look for"])
            and "contact" in message_lower
        ):
            # Extract search term
            words = message.split()
            search_term = "john"  # Default for testing
            for i, word in enumerate(words):
                if word.lower() in ["search", "find", "for"] and i + 1 < len(words):
                    search_term = words[i + 1].strip(".,!?")
                    break
            return ("search_contacts", {"query": search_term})
        elif "export" in message_lower and "contact" in message_lower:
            return ("export_contacts", {"format": "json"})

        return None

    def chat(self, message: str) -> str:
        """Return deterministic responses based on message patterns."""
        start_time = time.time()

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})

        logger.debug(f"Processing chat message: {message}")

        # Check if we should simulate a tool call
        tool_call = self._should_call_tool(message)
        if tool_call:
            tool_name, arguments = tool_call
            tool_result = self._simulate_tool_call(tool_name, arguments)

            # Generate response based on tool result
            if tool_name == "get_database_stats":
                response = f"You have {tool_result['contacts']} contacts, {tool_result['tags']} tags, and {tool_result['notes']} notes in your database."
            elif tool_name == "search_contacts":
                if isinstance(tool_result, list) and tool_result:
                    names = [contact.get("name", "Unknown") for contact in tool_result]
                    response = f"Found {len(tool_result)} contacts: {', '.join(names)}"
                else:
                    response = "No contacts found matching your search."
            elif tool_name == "export_contacts":
                response = f"Exported {tool_result['exported_count']} contacts to {tool_result['output_path']}"
            elif tool_name == "_get_contacts_with_images":
                if tool_result["success"]:
                    if tool_result["count"] > 0:
                        names = [
                            contact.get("name", "Unknown")
                            for contact in tool_result["contacts"][:3]
                        ]
                        names_str = ", ".join(names)
                        if tool_result["count"] > 3:
                            names_str += f" and {tool_result['count'] - 3} more"
                        response = f"Found {tool_result['count']} contacts with profile images: {names_str}"
                    else:
                        response = "No contacts with profile images found in your database."
                else:
                    response = f"Error getting contacts with images: {tool_result.get('error', 'Unknown error')}"
            elif tool_name == "_create_directory_from_contacts_with_images":
                if tool_result["success"]:
                    response = f"Created directory with {tool_result['contact_count']} contacts at {tool_result['output_path']}. You can view it at {tool_result['url']}"
                else:
                    response = (
                        f"Failed to create directory: {tool_result.get('error', 'Unknown error')}"
                    )
            else:
                response = f"Tool {tool_name} executed successfully: {json.dumps(tool_result)}"
        else:
            # Use pattern matching for response
            response = self._match_response_pattern(message)

        # Add response to history
        self.conversation_history.append({"role": "assistant", "content": response})

        elapsed = time.time() - start_time
        logger.debug(f"Chat response generated in {elapsed:.3f}s: {response[:100]}...")

        return response

    async def health_check(self, timeout: float = 2.0) -> bool:
        """Always return True for testing."""
        logger.debug("MockOllamaLLM health check - always returns True")
        return True

    async def preload_model(self) -> bool:
        """Always return True for testing."""
        logger.debug("MockOllamaLLM preload model - always returns True")
        return True

    def is_available(self) -> bool:
        """Always return True for testing."""
        return True

    def get_conversation_history(self) -> List[dict]:
        """Get conversation history for testing."""
        return self.conversation_history.copy()

    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        self.tool_call_history.clear()
        self.last_tool_called = None

    def get_tool_call_history(self) -> List[dict]:
        """Get history of simulated tool calls."""
        return self.tool_call_history.copy()

    def _get_contacts_with_images(self) -> Dict[str, Any]:
        """Mock the _get_contacts_with_images tool for testing."""
        self.last_tool_called = "_get_contacts_with_images"
        self.tool_call_history.append({"tool": "_get_contacts_with_images", "args": {}})

        try:
            # Use real API to get contacts with images
            contacts = self.api.get_contacts_with_images()

            # If no real contacts, provide mock data for testing
            if not contacts:
                contacts = [
                    {
                        "id": 1,
                        "name": "Mock Contact 1",
                        "email": "mock1@example.com",
                        "profile_image": b"mock_image_data_1",
                    },
                    {
                        "id": 2,
                        "name": "Mock Contact 2",
                        "email": "mock2@example.com",
                        "profile_image": b"mock_image_data_2",
                    },
                ]

            return {
                "success": True,
                "contacts": contacts,
                "count": len(contacts),
                "message": f"Found {len(contacts)} contacts with profile images",
            }

        except Exception as e:
            return {"success": False, "error": str(e), "contacts": [], "count": 0}

    def _create_directory_from_contacts_with_images(
        self, output_name: str = None
    ) -> Dict[str, Any]:
        """Mock the directory creation tool for testing."""
        self.last_tool_called = "_create_directory_from_contacts_with_images"
        self.tool_call_history.append(
            {
                "tool": "_create_directory_from_contacts_with_images",
                "args": {"output_name": output_name},
            }
        )

        try:
            # Get contacts first
            contacts_result = self._get_contacts_with_images()

            if not contacts_result["success"] or contacts_result["count"] == 0:
                return {"success": False, "error": "No contacts with images found"}

            contact_count = contacts_result["count"]
            output_path = f"/mock/directories/{output_name or 'contacts_with_images'}"

            return {
                "success": True,
                "output_path": output_path,
                "url": f"file://{output_path}/index.html",
                "contact_count": contact_count,
                "performance": {
                    "query_time_ms": 5.0,
                    "directory_time_ms": 10.0,
                    "total_time_ms": 15.0,
                },
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
