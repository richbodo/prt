"""
PRT LLM Commands

This module provides a command-line interface specifically designed for LLM use.
It allows direct function calls with arguments rather than interactive prompts.
"""

import sys
import json
from .api import PRTAPI


class PRTLLMCommands:
    """Command interface for LLM use."""
    
    def __init__(self):
        self.api = PRTAPI()
    
    def search_contacts(self, query: str) -> str:
        """Search contacts and return JSON result."""
        contacts = self.api.search_contacts(query)
        return json.dumps(contacts, indent=2)
    
    def search_tags(self, query: str) -> str:
        """Search tags and return JSON result."""
        tags = self.api.search_tags(query)
        return json.dumps(tags, indent=2)
    
    def search_notes(self, query: str) -> str:
        """Search notes and return JSON result."""
        notes = self.api.search_notes(query)
        return json.dumps(notes, indent=2)
    
    def get_contacts_by_tag(self, tag_name: str) -> str:
        """Get contacts by tag and return JSON result."""
        contacts = self.api.get_contacts_by_tag(tag_name)
        return json.dumps(contacts, indent=2)
    
    def get_contacts_by_note(self, note_title: str) -> str:
        """Get contacts by note and return JSON result."""
        contacts = self.api.get_contacts_by_note(note_title)
        return json.dumps(contacts, indent=2)
    
    def get_contact_details(self, contact_id: int) -> str:
        """Get contact details and return JSON result."""
        contact = self.api.get_contact_details(contact_id)
        return json.dumps(contact, indent=2) if contact else "Contact not found"
    
    def list_all_contacts(self) -> str:
        """List all contacts and return JSON result."""
        contacts = self.api.list_all_contacts()
        return json.dumps(contacts, indent=2)
    
    def list_all_tags(self) -> str:
        """List all tags and return JSON result."""
        tags = self.api.list_all_tags()
        return json.dumps(tags, indent=2)
    
    def list_all_notes(self) -> str:
        """List all notes and return JSON result."""
        notes = self.api.list_all_notes()
        return json.dumps(notes, indent=2)
    
    def add_tag_to_contact(self, contact_id: int, tag_name: str) -> str:
        """Add tag to contact and return result."""
        success = self.api.add_tag_to_contact(contact_id, tag_name)
        return f"Success: {success}"
    
    def remove_tag_from_contact(self, contact_id: int, tag_name: str) -> str:
        """Remove tag from contact and return result."""
        success = self.api.remove_tag_from_contact(contact_id, tag_name)
        return f"Success: {success}"
    
    def add_note_to_contact(self, contact_id: int, note_title: str, note_content: str) -> str:
        """Add note to contact and return result."""
        success = self.api.add_note_to_contact(contact_id, note_title, note_content)
        return f"Success: {success}"
    
    def remove_note_from_contact(self, contact_id: int, note_title: str) -> str:
        """Remove note from contact and return result."""
        success = self.api.remove_note_from_contact(contact_id, note_title)
        return f"Success: {success}"
    
    def create_tag(self, name: str) -> str:
        """Create a new tag and return JSON result."""
        tag = self.api.create_tag(name)
        return json.dumps(tag, indent=2) if tag else "Tag already exists"
    
    def delete_tag(self, name: str) -> str:
        """Delete a tag and return result."""
        success = self.api.delete_tag(name)
        return f"Success: {success}"
    
    def create_note(self, title: str, content: str) -> str:
        """Create a new note and return JSON result."""
        note = self.api.create_note(title, content)
        return json.dumps(note, indent=2) if note else "Note already exists"
    
    def update_note(self, title: str, content: str) -> str:
        """Update a note and return result."""
        success = self.api.update_note(title, content)
        return f"Success: {success}"
    
    def delete_note(self, title: str) -> str:
        """Delete a note and return result."""
        success = self.api.delete_note(title)
        return f"Success: {success}"
    
    def get_help(self) -> str:
        """Return help information for all available commands."""
        help_text = """
Available PRT LLM Commands:

SEARCH COMMANDS:
- search_contacts(query: str) - Search contacts by name
- search_tags(query: str) - Search tags by name
- search_notes(query: str) - Search notes by title or content
- get_contacts_by_tag(tag_name: str) - Get all contacts with a specific tag
- get_contacts_by_note(note_title: str) - Get all contacts with a specific note

LIST COMMANDS:
- list_all_contacts() - List all contacts
- list_all_tags() - List all tags
- list_all_notes() - List all notes
- get_contact_details(contact_id: int) - Get detailed info about a contact

RELATIONSHIP COMMANDS:
- add_tag_to_contact(contact_id: int, tag_name: str) - Add tag to contact
- remove_tag_from_contact(contact_id: int, tag_name: str) - Remove tag from contact
- add_note_to_contact(contact_id: int, note_title: str, note_content: str) - Add note to contact
- remove_note_from_contact(contact_id: int, note_title: str) - Remove note from contact

MANAGEMENT COMMANDS:
- create_tag(name: str) - Create a new tag
- delete_tag(name: str) - Delete a tag
- create_note(title: str, content: str) - Create a new note
- update_note(title: str, content: str) - Update a note's content
- delete_note(title: str) - Delete a note

All commands return JSON results except for success/failure messages.
"""
        return help_text


def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python -m prt_src.llm_commands <command> [args...]")
        print("Use 'help' command to see available commands")
        sys.exit(1)
    
    commands = PRTLLMCommands()
    command = sys.argv[1]
    args = sys.argv[2:]
    
    try:
        if command == "help":
            print(commands.get_help())
        elif command == "search_contacts":
            if len(args) < 1:
                print("Usage: search_contacts <query>")
                sys.exit(1)
            print(commands.search_contacts(args[0]))
        elif command == "search_tags":
            if len(args) < 1:
                print("Usage: search_tags <query>")
                sys.exit(1)
            print(commands.search_tags(args[0]))
        elif command == "search_notes":
            if len(args) < 1:
                print("Usage: search_notes <query>")
                sys.exit(1)
            print(commands.search_notes(args[0]))
        elif command == "get_contacts_by_tag":
            if len(args) < 1:
                print("Usage: get_contacts_by_tag <tag_name>")
                sys.exit(1)
            print(commands.get_contacts_by_tag(args[0]))
        elif command == "get_contacts_by_note":
            if len(args) < 1:
                print("Usage: get_contacts_by_note <note_title>")
                sys.exit(1)
            print(commands.get_contacts_by_note(args[0]))
        elif command == "get_contact_details":
            if len(args) < 1:
                print("Usage: get_contact_details <contact_id>")
                sys.exit(1)
            print(commands.get_contact_details(int(args[0])))
        elif command == "list_all_contacts":
            print(commands.list_all_contacts())
        elif command == "list_all_tags":
            print(commands.list_all_tags())
        elif command == "list_all_notes":
            print(commands.list_all_notes())
        elif command == "add_tag_to_contact":
            if len(args) < 2:
                print("Usage: add_tag_to_contact <contact_id> <tag_name>")
                sys.exit(1)
            print(commands.add_tag_to_contact(int(args[0]), args[1]))
        elif command == "remove_tag_from_contact":
            if len(args) < 2:
                print("Usage: remove_tag_from_contact <contact_id> <tag_name>")
                sys.exit(1)
            print(commands.remove_tag_from_contact(int(args[0]), args[1]))
        elif command == "add_note_to_contact":
            if len(args) < 3:
                print("Usage: add_note_to_contact <contact_id> <note_title> <note_content>")
                sys.exit(1)
            print(commands.add_note_to_contact(int(args[0]), args[1], args[2]))
        elif command == "remove_note_from_contact":
            if len(args) < 2:
                print("Usage: remove_note_from_contact <contact_id> <note_title>")
                sys.exit(1)
            print(commands.remove_note_from_contact(int(args[0]), args[1]))
        elif command == "create_tag":
            if len(args) < 1:
                print("Usage: create_tag <name>")
                sys.exit(1)
            print(commands.create_tag(args[0]))
        elif command == "delete_tag":
            if len(args) < 1:
                print("Usage: delete_tag <name>")
                sys.exit(1)
            print(commands.delete_tag(args[0]))
        elif command == "create_note":
            if len(args) < 2:
                print("Usage: create_note <title> <content>")
                sys.exit(1)
            print(commands.create_note(args[0], args[1]))
        elif command == "update_note":
            if len(args) < 2:
                print("Usage: update_note <title> <content>")
                sys.exit(1)
            print(commands.update_note(args[0], args[1]))
        elif command == "delete_note":
            if len(args) < 1:
                print("Usage: delete_note <title>")
                sys.exit(1)
            print(commands.delete_note(args[0]))
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' command to see available commands")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
