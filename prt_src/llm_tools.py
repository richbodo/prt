"""
Centralized LLM Tool Registry for PRT

This module provides a centralized registry eliminating tool definition duplication
across different LLM providers (Ollama, LlamaCpp, etc).
"""

from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

from prt_src.api import PRTAPI
from prt_src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Tool:
    """Represents a tool that can be called by the LLM."""

    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable


class LLMToolRegistry:
    """Centralized registry eliminating tool definition duplication."""

    def __init__(self, api: PRTAPI, disabled_tools: Optional[Set[str]] = None):
        """Initialize the tool registry.

        Args:
            api: PRTAPI instance for database operations
            disabled_tools: Set of tool names to disable/exclude
        """
        self.api = api
        self.disabled_tools = disabled_tools or set()

    def get_all_tools(self) -> List[Tool]:
        """Return all tools with consistent definitions."""
        tools = [
            *self._create_read_tools(),  # 11 search/info tools
            *self._create_write_tools(),  # 13 CRUD tools with backups
        ]

        # Filter out disabled tools
        if self.disabled_tools:
            enabled_tools = [t for t in tools if t.name not in self.disabled_tools]
            disabled_missing = {t.name for t in tools} & self.disabled_tools
            if disabled_missing:
                logger.info(
                    "[LLM] Tool(s) removed from availability: %s",
                    ", ".join(sorted(disabled_missing)),
                )
            return enabled_tools

        return tools

    def _create_read_tools(self) -> List[Tool]:
        """Create read-only tools (search, info, list operations)."""
        return [
            Tool(
                name="search_contacts",
                description="Search for contacts. Pass empty string to get ALL contacts.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": 'Search term. Use "" to return all contacts.',
                        }
                    },
                    "required": [],
                },
                function=self.api.search_contacts,
            ),
            Tool(
                name="list_all_contacts",
                description="Get a complete list of all contacts.",
                parameters={"type": "object", "properties": {}},
                function=self.api.list_all_contacts,
            ),
            Tool(
                name="list_all_tags",
                description="Get a complete list of all tags.",
                parameters={"type": "object", "properties": {}},
                function=self.api.list_all_tags,
            ),
            Tool(
                name="list_all_notes",
                description="Get a complete list of all notes.",
                parameters={"type": "object", "properties": {}},
                function=self.api.list_all_notes,
            ),
            Tool(
                name="get_database_stats",
                description="Get database statistics.",
                parameters={"type": "object", "properties": {}},
                function=self.api.get_database_stats,
            ),
            Tool(
                name="get_database_schema",
                description="Get complete database schema information.",
                parameters={"type": "object", "properties": {}},
                function=self.api.get_database_schema,
            ),
            Tool(
                name="get_contact_details",
                description="Get detailed information about a specific contact by ID.",
                parameters={
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "integer", "description": "ID of the contact"}
                    },
                    "required": ["contact_id"],
                },
                function=self.api.get_contact_details,
            ),
            Tool(
                name="search_tags",
                description="Search for tags by name.",
                parameters={
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Search term"}},
                    "required": ["query"],
                },
                function=self.api.search_tags,
            ),
            Tool(
                name="search_notes",
                description="Search for notes by title or content.",
                parameters={
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "Search term"}},
                    "required": ["query"],
                },
                function=self.api.search_notes,
            ),
            Tool(
                name="get_contacts_by_tag",
                description="Get all contacts that have a specific tag.",
                parameters={
                    "type": "object",
                    "properties": {"tag_name": {"type": "string", "description": "Tag name"}},
                    "required": ["tag_name"],
                },
                function=self.api.get_contacts_by_tag,
            ),
            Tool(
                name="get_contacts_by_note",
                description="Get all contacts that have a specific note.",
                parameters={
                    "type": "object",
                    "properties": {"note_title": {"type": "string", "description": "Note title"}},
                    "required": ["note_title"],
                },
                function=self.api.get_contacts_by_note,
            ),
        ]

    def _create_write_tools(self) -> List[Tool]:
        """Create write operations tools (CRUD with backups)."""
        return [
            # Tag operations
            Tool(
                name="add_tag_to_contact",
                description="Add a tag to a contact.",
                parameters={
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "integer", "description": "ID of the contact"},
                        "tag_name": {"type": "string", "description": "Tag to add"},
                    },
                    "required": ["contact_id", "tag_name"],
                },
                function=self.api.add_tag_to_contact,
            ),
            Tool(
                name="remove_tag_from_contact",
                description="Remove a tag from a contact.",
                parameters={
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "integer", "description": "ID of the contact"},
                        "tag_name": {"type": "string", "description": "Tag to remove"},
                    },
                    "required": ["contact_id", "tag_name"],
                },
                function=self.api.remove_tag_from_contact,
            ),
            Tool(
                name="create_tag",
                description="Create a new tag.",
                parameters={
                    "type": "object",
                    "properties": {"name": {"type": "string", "description": "Tag name"}},
                    "required": ["name"],
                },
                function=self.api.create_tag,
            ),
            Tool(
                name="delete_tag",
                description="Delete a tag.",
                parameters={
                    "type": "object",
                    "properties": {"name": {"type": "string", "description": "Tag name"}},
                    "required": ["name"],
                },
                function=self.api.delete_tag,
            ),
            # Note operations
            Tool(
                name="add_note_to_contact",
                description="Add a note to a contact.",
                parameters={
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "integer", "description": "ID of the contact"},
                        "note_title": {"type": "string", "description": "Note title"},
                        "note_content": {"type": "string", "description": "Note content"},
                    },
                    "required": ["contact_id", "note_title", "note_content"],
                },
                function=self.api.add_note_to_contact,
            ),
            Tool(
                name="remove_note_from_contact",
                description="Remove a note from a contact.",
                parameters={
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "integer", "description": "ID of the contact"},
                        "note_title": {"type": "string", "description": "Note title"},
                    },
                    "required": ["contact_id", "note_title"],
                },
                function=self.api.remove_note_from_contact,
            ),
            Tool(
                name="create_note",
                description="Create a new note.",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Note title"},
                        "content": {"type": "string", "description": "Note content"},
                    },
                    "required": ["title", "content"],
                },
                function=self.api.create_note,
            ),
            Tool(
                name="update_note",
                description="Update an existing note.",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Note title"},
                        "content": {"type": "string", "description": "New content"},
                    },
                    "required": ["title", "content"],
                },
                function=self.api.update_note,
            ),
            Tool(
                name="delete_note",
                description="Delete a note.",
                parameters={
                    "type": "object",
                    "properties": {"title": {"type": "string", "description": "Note title"}},
                    "required": ["title"],
                },
                function=self.api.delete_note,
            ),
            # Relationship operations
            Tool(
                name="add_contact_relationship",
                description="Create a relationship between two contacts.",
                parameters={
                    "type": "object",
                    "properties": {
                        "from_contact_name": {"type": "string", "description": "From contact"},
                        "to_contact_name": {"type": "string", "description": "To contact"},
                        "type_key": {"type": "string", "description": "Relationship type"},
                    },
                    "required": ["from_contact_name", "to_contact_name", "type_key"],
                },
                function=self.api.add_contact_relationship,
            ),
            Tool(
                name="remove_contact_relationship",
                description="Remove a relationship between two contacts.",
                parameters={
                    "type": "object",
                    "properties": {
                        "from_contact_name": {"type": "string", "description": "From contact"},
                        "to_contact_name": {"type": "string", "description": "To contact"},
                        "type_key": {"type": "string", "description": "Relationship type"},
                    },
                    "required": ["from_contact_name", "to_contact_name", "type_key"],
                },
                function=self.api.remove_contact_relationship,
            ),
            # Backup operations
            Tool(
                name="create_backup_with_comment",
                description="Create a manual database backup.",
                parameters={
                    "type": "object",
                    "properties": {"comment": {"type": "string", "description": "Backup comment"}},
                    "required": [],
                },
                function=self.api.create_backup_with_comment,
            ),
        ]

    @staticmethod
    def get_write_tool_names() -> Set[str]:
        """Get set of tool names that perform write operations."""
        return {
            "add_tag_to_contact",
            "remove_tag_from_contact",
            "create_tag",
            "delete_tag",
            "add_note_to_contact",
            "remove_note_from_contact",
            "create_note",
            "update_note",
            "delete_note",
            "add_contact_relationship",
            "remove_contact_relationship",
            "execute_sql",  # Provider-specific implementation
        }

    def get_tool_by_name(self, tool_name: str) -> Optional[Tool]:
        """Get tool by name from registry.

        Args:
            tool_name: Name of tool to find

        Returns:
            Tool object or None if not found
        """
        for tool in self.get_all_tools():
            if tool.name == tool_name:
                return tool
        return None
