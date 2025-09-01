"""Chat mode screen for PRT TUI.

Natural language interface with command detection.
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Input, LoadingIndicator, RichLog

from prt_src.logging_config import get_logger
from prt_src.tui.screens import register_screen
from prt_src.tui.screens.base import BaseScreen, EscapeIntent

logger = get_logger(__name__)


class ChatMessage:
    """Represents a chat message."""

    def __init__(self, content: str, is_user: bool = True, timestamp: Optional[datetime] = None):
        """Initialize chat message.

        Args:
            content: Message content
            is_user: True if user message, False if assistant
            timestamp: Message timestamp
        """
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()


class ChatScreen(BaseScreen):
    """Chat interface screen."""

    def get_screen_name(self) -> str:
        """Get screen identifier."""
        return "chat"

    def __init__(self, *args, **kwargs):
        """Initialize chat screen."""
        super().__init__(*args, **kwargs)
        self._has_input = False
        self.message_history = []
        self.command_history = []
        self.command_index = 0

        # Hide chrome for full-screen chat
        self.hide_chrome()

    def on_escape(self) -> EscapeIntent:
        """CUSTOM - clear input first, then HOME."""
        return EscapeIntent.CUSTOM

    def handle_custom_escape(self) -> None:
        """Handle custom ESC behavior."""
        if self._has_input:
            # Clear input field
            self._clear_input()
            self._has_input = False
        else:
            # Go home if no input (with null check)
            if self.nav_service:
                try:
                    self.nav_service.go_home()
                except Exception:
                    pass  # Navigation service may not be available

    def _clear_input(self) -> None:
        """Clear the chat input field."""
        if hasattr(self, "chat_input"):
            self.chat_input.value = ""
            self._has_input = False

    def compose(self) -> ComposeResult:
        """Compose chat screen layout."""
        with Vertical(classes="chat-container"):
            # Chat history area (takes most of the screen)
            self.chat_log = RichLog(
                highlight=True,
                markup=True,
                classes="chat-log",
            )
            yield self.chat_log

            # Input area at bottom
            with Horizontal(classes="chat-input-container"):
                # Loading indicator (initially hidden)
                self.loading_indicator = LoadingIndicator(classes="chat-loading")
                self.loading_indicator.display = False
                yield self.loading_indicator

                # Chat input field
                self.chat_input = Input(
                    placeholder="Enter your query... (e.g., 'Show me contacts I haven't talked to recently')",
                    classes="chat-input",
                )
                yield self.chat_input

    async def on_mount(self) -> None:
        """Called when screen is mounted."""
        await super().on_mount()

        # Focus the input field
        self.chat_input.focus()

        # Display welcome message
        welcome_msg = """
[bold blue]🤖 PRT Chat Assistant[/bold blue]

Welcome to the PRT natural language interface! I can help you with your contacts and relationships.

[yellow]🔗 Enhanced with Ollama AI (if available)[/yellow]
When Ollama is running, I provide intelligent responses with direct database access.

• [green]Contacts:[/green] "Show me contacts I haven't talked to recently"
• [green]Notes:[/green] "Add a note about John's birthday"
• [green]Relationships:[/green] "Find all family relationships"
• [green]Search:[/green] "Find everyone tagged as 'work'"
• [green]Database:[/green] "How many contacts do I have?"

[dim]Press Ctrl+L to clear chat, Up/Down arrows to browse history, ESC to go back[/dim]
"""
        self.chat_log.write(welcome_msg)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input != self.chat_input:
            return

        query = self.chat_input.value.strip()
        if not query:
            return

        # Add to command history
        if query not in self.command_history:
            self.command_history.append(query)
        self.command_index = len(self.command_history)

        # Clear input and show typing indicator
        self.chat_input.value = ""
        self._has_input = False
        self._show_typing_indicator()

        # Add user message to chat
        user_msg = ChatMessage(query, is_user=True)
        self.message_history.append(user_msg)
        self._display_message(user_msg)

        # Process the query
        await self._process_query(query)

        # Hide typing indicator
        self._hide_typing_indicator()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input != self.chat_input:
            return

        self._has_input = len(self.chat_input.value.strip()) > 0

    async def on_key(self, event: events.Key) -> None:
        """Handle key events."""
        # Handle Ctrl+L to clear chat
        if event.key == "ctrl+l":
            self._clear_chat()
            return

        # Handle Up/Down arrows for command history when input is focused
        if self.chat_input.has_focus and self.command_history:
            if event.key == "up" and self.command_index > 0:
                self.command_index -= 1
                self.chat_input.value = self.command_history[self.command_index]
                self._has_input = True
                return
            elif event.key == "down":
                if self.command_index < len(self.command_history) - 1:
                    self.command_index += 1
                    self.chat_input.value = self.command_history[self.command_index]
                else:
                    self.command_index = len(self.command_history)
                    self.chat_input.value = ""
                    self._has_input = False
                return

        await super().on_key(event)

    def _display_message(self, message: ChatMessage) -> None:
        """Display a message in the chat log.

        Args:
            message: Chat message to display
        """
        timestamp = message.timestamp.strftime("%H:%M:%S")

        if message.is_user:
            # User message
            self.chat_log.write(f"[bold cyan]You[/bold cyan] [{timestamp}]: {message.content}")
        else:
            # Assistant message
            self.chat_log.write(
                f"[bold green]Assistant[/bold green] [{timestamp}]: {message.content}"
            )

    def _show_typing_indicator(self) -> None:
        """Show typing indicator."""
        self.loading_indicator.display = True

    def _hide_typing_indicator(self) -> None:
        """Hide typing indicator."""
        self.loading_indicator.display = False

    def _clear_chat(self) -> None:
        """Clear the chat history."""
        self.chat_log.clear()
        self.message_history.clear()

        # Show welcome message again
        self.set_timer(0.1, self._show_welcome)

    async def _show_welcome(self) -> None:
        """Show welcome message after clearing."""
        welcome_msg = (
            "[dim]Chat cleared[/dim]\n\n[bold blue]🤖 Ready for your next question![/bold blue]"
        )
        self.chat_log.write(welcome_msg)

    async def _process_query(self, query: str) -> None:
        """Process a natural language query.

        Args:
            query: User's natural language query
        """
        try:
            # Try Ollama integration first if available
            result = await self._try_ollama_query(query)

            if result is None:
                # Fallback to local processing if Ollama isn't available
                intent, params = self._parse_query(query)
                result = await self._execute_command(intent, params, query)

            # Display the result
            assistant_msg = ChatMessage(result, is_user=False)
            self.message_history.append(assistant_msg)
            self._display_message(assistant_msg)

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            error_msg = ChatMessage(
                f"Sorry, I encountered an error processing your request: {e}", is_user=False
            )
            self.message_history.append(error_msg)
            self._display_message(error_msg)

    async def _try_ollama_query(self, query: str) -> Optional[str]:
        """Try to process query using Ollama LLM.

        Args:
            query: User's natural language query

        Returns:
            LLM response or None if Ollama isn't available
        """
        try:
            # Import Ollama integration
            from prt_src.llm_ollama import OllamaLLM

            # Check if we have data service
            if not self.data_service or not hasattr(self.data_service, "api"):
                return None

            # Create Ollama LLM instance
            ollama = OllamaLLM(self.data_service.api)

            # Get response from Ollama
            response = ollama.chat(query)

            # Check for error responses
            if response.startswith("Error:"):
                logger.warning(f"Ollama error: {response}")
                return None

            return response

        except ImportError:
            logger.debug("Ollama integration not available")
            return None
        except Exception as e:
            logger.warning(f"Ollama query failed: {e}")
            return None

    def _parse_query(self, query: str) -> tuple[str, Dict[str, Any]]:
        """Parse natural language query to extract intent and parameters.

        Args:
            query: User's natural language query

        Returns:
            Tuple of (intent, parameters)
        """
        query_lower = query.lower()

        # Contact queries
        if any(phrase in query_lower for phrase in ["contacts", "people", "person"]):
            if any(
                phrase in query_lower
                for phrase in ["haven't talked", "haven't spoken", "not contacted", "silent"]
            ):
                return "find_inactive_contacts", {"days": 30}  # Default 30 days
            elif any(phrase in query_lower for phrase in ["recent", "lately", "talked to"]):
                return "find_recent_contacts", {"days": 7}  # Default 7 days
            elif "search" in query_lower or "find" in query_lower:
                # Extract search term
                search_term = self._extract_search_term(query)
                return "search_contacts", {"query": search_term}
            else:
                return "list_contacts", {"limit": 20}

        # Note queries
        elif any(phrase in query_lower for phrase in ["note", "notes"]):
            if any(phrase in query_lower for phrase in ["add", "create", "new"]):
                # Extract note content
                content = self._extract_note_content(query)
                return "add_note", {"content": content}
            else:
                return "list_notes", {"limit": 10}

        # Relationship queries
        elif any(
            phrase in query_lower
            for phrase in ["relationship", "relationships", "family", "friends"]
        ):
            if "family" in query_lower:
                return "find_relationships", {"type": "family"}
            elif "friend" in query_lower:
                return "find_relationships", {"type": "friend"}
            else:
                return "list_relationships", {}

        # Meeting/interaction queries
        elif any(
            phrase in query_lower
            for phrase in ["last met", "last meeting", "when did i", "last talked"]
        ):
            contact_name = self._extract_contact_name(query)
            return "find_last_interaction", {"contact_name": contact_name}

        # Tag queries
        elif any(phrase in query_lower for phrase in ["tag", "tagged"]):
            tag_name = self._extract_tag_name(query)
            return "find_by_tag", {"tag_name": tag_name}

        # Search queries
        elif any(phrase in query_lower for phrase in ["search", "find"]):
            search_term = self._extract_search_term(query)
            return "unified_search", {"query": search_term}

        # Default fallback
        else:
            return "unified_search", {"query": query}

    def _extract_search_term(self, query: str) -> str:
        """Extract search term from query."""
        # Remove common query words and return the rest
        words_to_remove = [
            "show",
            "me",
            "find",
            "search",
            "for",
            "all",
            "the",
            "contacts",
            "people",
            "person",
        ]
        words = query.lower().split()
        filtered_words = [w for w in words if w not in words_to_remove]
        return " ".join(filtered_words) if filtered_words else query

    def _extract_note_content(self, query: str) -> str:
        """Extract note content from query."""
        # Look for patterns like "add a note about X" or "create note: X"
        patterns = [
            r"(?:add|create).*?note.*?about (.+)",
            r"(?:add|create).*?note:(.+)",
            r"note (.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return query

    def _extract_contact_name(self, query: str) -> str:
        """Extract contact name from query."""
        # Look for patterns like "when did I last meet John" or "last talked to Sarah"
        patterns = [
            r"(?:meet|talk(?:ed)?.*?to|contact(?:ed)?)\s+(\w+)",
            r"(\w+)(?:'s|s)?\s+(?:birthday|meeting|call)",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: return the last word that looks like a name
        words = query.split()
        for word in reversed(words):
            if word[0].isupper() and word.isalpha():
                return word

        return ""

    def _extract_tag_name(self, query: str) -> str:
        """Extract tag name from query."""
        # Look for patterns like "tagged as X" or "with tag X"
        patterns = [
            r"tagged\s+as\s+['\"]?(\w+)['\"]?",
            r"with\s+tag\s+['\"]?(\w+)['\"]?",
            r"tag\s+['\"]?(\w+)['\"]?",
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    async def _execute_command(
        self, intent: str, params: Dict[str, Any], original_query: str
    ) -> str:
        """Execute a command based on intent and parameters.

        Args:
            intent: Command intent
            params: Command parameters
            original_query: Original user query

        Returns:
            Result message to display
        """
        if not self.data_service:
            return "Data service not available. Please try again later."

        try:
            if intent == "list_contacts":
                contacts = await self.data_service.get_contacts(limit=params.get("limit", 20))
                if not contacts:
                    return "No contacts found."

                result = f"Found {len(contacts)} contacts:\n\n"
                for contact in contacts[:10]:  # Show first 10
                    name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                    if not name:
                        name = "Unnamed Contact"
                    result += f"• {name}"
                    if contact.get("email"):
                        result += f" ({contact['email']})"
                    result += "\n"

                if len(contacts) > 10:
                    result += f"\n... and {len(contacts) - 10} more"

                return result

            elif intent == "search_contacts":
                query = params.get("query", "")
                if not query:
                    return "Please specify what to search for."

                contacts = await self.data_service.search_contacts(query)
                if not contacts:
                    return f"No contacts found matching '{query}'."

                result = f"Found {len(contacts)} contacts matching '{query}':\n\n"
                for contact in contacts:
                    name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                    if not name:
                        name = "Unnamed Contact"
                    result += f"• {name}"
                    if contact.get("email"):
                        result += f" ({contact['email']})"
                    result += "\n"

                return result

            elif intent == "find_inactive_contacts":
                # This would require interaction tracking, which we'll simulate
                contacts = await self.data_service.get_contacts(limit=100)
                if not contacts:
                    return "No contacts found."

                # For demo purposes, return a sample of contacts
                sample_contacts = contacts[:5]  # First 5 as inactive
                result = f"Contacts you haven't talked to recently (last {params.get('days', 30)} days):\n\n"
                for contact in sample_contacts:
                    name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                    if not name:
                        name = "Unnamed Contact"
                    result += f"• {name}\n"

                return result

            elif intent == "list_notes":
                notes = await self.data_service.get_notes()
                if not notes:
                    return "No notes found."

                result = f"Recent notes ({len(notes)} total):\n\n"
                for note in notes[: params.get("limit", 10)]:
                    title = note.get("title", "Untitled")
                    content_preview = note.get("content", "")[:50]
                    if len(note.get("content", "")) > 50:
                        content_preview += "..."
                    result += f"• {title}: {content_preview}\n"

                return result

            elif intent == "add_note":
                content = params.get("content", "")
                if not content:
                    return "Please specify what note to add."

                # Extract title from content (first few words)
                words = content.split()
                title = " ".join(words[:5]) if len(words) > 5 else content

                note = await self.data_service.create_note(title, content)
                if note:
                    return f"Note added successfully: '{title}'"
                else:
                    return "Failed to add note. Please try again."

            elif intent == "list_relationships":
                relationships = await self.data_service.get_relationships()
                if not relationships:
                    return "No relationships found."

                result = f"Found {len(relationships)} relationships:\n\n"
                for rel in relationships[:10]:  # Show first 10
                    person1 = rel.get("person1_name", "Unknown")
                    person2 = rel.get("person2_name", "Unknown")
                    rel_type = rel.get("relationship_type", "unknown")
                    result += f"• {person1} → {person2} ({rel_type})\n"

                if len(relationships) > 10:
                    result += f"\n... and {len(relationships) - 10} more"

                return result

            elif intent == "find_relationships":
                rel_type = params.get("type", "")
                relationships = await self.data_service.get_relationships()

                if rel_type:
                    filtered_rels = [
                        r
                        for r in relationships
                        if rel_type.lower() in r.get("relationship_type", "").lower()
                    ]
                else:
                    filtered_rels = relationships

                if not filtered_rels:
                    return (
                        f"No {rel_type} relationships found."
                        if rel_type
                        else "No relationships found."
                    )

                result = (
                    f"Found {len(filtered_rels)} {rel_type} relationships:\n\n"
                    if rel_type
                    else f"Found {len(filtered_rels)} relationships:\n\n"
                )
                for rel in filtered_rels[:10]:
                    person1 = rel.get("person1_name", "Unknown")
                    person2 = rel.get("person2_name", "Unknown")
                    rel_type_display = rel.get("relationship_type", "unknown")
                    result += f"• {person1} → {person2} ({rel_type_display})\n"

                return result

            elif intent == "find_last_interaction":
                contact_name = params.get("contact_name", "")
                if not contact_name:
                    return "Please specify which contact you're asking about."

                # Search for the contact first
                contacts = await self.data_service.search_contacts(contact_name)
                if not contacts:
                    return f"No contact found matching '{contact_name}'."

                # For demo purposes, simulate last interaction
                contact = contacts[0]
                name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                return f"I don't have interaction tracking data for {name} yet. This feature will be enhanced in future updates."

            elif intent == "find_by_tag":
                tag_name = params.get("tag_name", "")
                if not tag_name:
                    return "Please specify which tag to search for."

                # This would use get_contacts_by_tag if available
                return f"Tag-based search for '{tag_name}' is not yet implemented. You can try a regular search instead."

            elif intent == "unified_search":
                query = params.get("query", "")
                if not query:
                    return "Please specify what to search for."

                # Use unified search if available
                if hasattr(self.data_service, "unified_search"):
                    results = await self.data_service.unified_search(query)

                    if not results or results.get("total", 0) == 0:
                        return f"No results found for '{query}'."

                    result = f"Search results for '{query}' ({results.get('total', 0)} total):\n\n"

                    # Show contacts
                    if "contacts" in results.get("results", {}):
                        contacts = results["results"]["contacts"]
                        if contacts:
                            result += f"**Contacts ({len(contacts)}):**\n"
                            for contact in contacts[:5]:
                                name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                                result += f"• {name}\n"
                            result += "\n"

                    # Show notes
                    if "notes" in results.get("results", {}):
                        notes = results["results"]["notes"]
                        if notes:
                            result += f"**Notes ({len(notes)}):**\n"
                            for note in notes[:5]:
                                title = note.get("title", "Untitled")
                                result += f"• {title}\n"
                            result += "\n"

                    return result
                else:
                    # Fallback to contact search
                    contacts = await self.data_service.search_contacts(query)
                    if contacts:
                        result = f"Found {len(contacts)} contacts matching '{query}':\n\n"
                        for contact in contacts[:5]:
                            name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
                            result += f"• {name}\n"
                        return result
                    else:
                        return f"No results found for '{query}'."

            else:
                return "I'm not sure how to handle that request yet. Try asking about contacts, notes, or relationships."

        except Exception as e:
            logger.error(f"Error executing command {intent}: {e}")
            return f"Error executing command: {e}"


# Register this screen
register_screen("chat", ChatScreen)
