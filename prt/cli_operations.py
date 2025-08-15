"""
PRT Regular Operations CLI

This module provides the main menu and operations interface for PRT
after the initial setup is complete.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from typing import Optional, List, Dict, Any
from .api import PRTAPI

console = Console()


class PRTCLI:
    """Main CLI interface for PRT operations."""
    
    def __init__(self):
        self.api = PRTAPI()
    
    def show_main_menu(self):
        """Display the main menu and handle user selection."""
        while True:
            console.print("\n" + "="*50)
            console.print("PRT - Personal Relationship Toolkit", style="bold blue")
            console.print("="*50)
            console.print()
            console.print("1. Search & Browse")
            console.print("2. Manage Tags & Notes")
            console.print("3. Chat Mode")
            console.print("4. Exit")
            console.print()
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                self.search_and_browse_menu()
            elif choice == "2":
                self.manage_tags_notes_menu()
            elif choice == "3":
                self.enter_chat_mode()
            elif choice == "4":
                console.print("Goodbye!", style="green")
                break
    
    def search_and_browse_menu(self):
        """Search and browse menu."""
        while True:
            console.print("\n" + "-"*30)
            console.print("Search & Browse", style="bold blue")
            console.print("-"*30)
            console.print()
            console.print("1. Search contacts")
            console.print("2. Search tags")
            console.print("3. Search notes")
            console.print("4. Browse all contacts")
            console.print("5. Back to main menu")
            console.print()
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                self.search_contacts()
            elif choice == "2":
                self.search_tags()
            elif choice == "3":
                self.search_notes()
            elif choice == "4":
                self.browse_all_contacts()
            elif choice == "5":
                break
    
    def search_contacts(self):
        """Search contacts by name."""
        query = Prompt.ask("Enter contact name to search")
        contacts = self.api.search_contacts(query)
        
        if not contacts:
            console.print("No contacts found.", style="yellow")
            return
        
        # Show preview for multiple contacts
        if len(contacts) > 3:
            console.print(f"\nFound {len(contacts)} contacts matching '{query}':", style="bold blue")
            console.print(f"Preview (showing first 3):", style="cyan")
            
            for contact in contacts[:3]:
                console.print(f"  • {contact['name']}", style="green")
                if contact['email']:
                    console.print(f"    Email: {contact['email']}", style="dim")
                if contact['relationship_info']['tags']:
                    console.print(f"    Tags: {', '.join(contact['relationship_info']['tags'])}", style="yellow")
                if contact['relationship_info']['notes']:
                    note_titles = [note['title'] for note in contact['relationship_info']['notes']]
                    console.print(f"    Notes: {', '.join(note_titles)}", style="blue")
            
            if Confirm.ask(f"\nShow all {len(contacts)} contacts?"):
                self.display_contacts(contacts, f"All contacts matching '{query}'")
                self.handle_contact_selection(contacts)
        else:
            # If 3 or fewer, show them directly
            self.display_contacts(contacts, f"Contacts matching '{query}'")
            self.handle_contact_selection(contacts)
    
    def search_tags(self):
        """Search tags and show associated contacts."""
        query = Prompt.ask("Enter tag name to search")
        tags = self.api.search_tags(query)
        
        if not tags:
            console.print("No tags found.", style="yellow")
            return
        
        # Display tags with previews
        for tag in tags:
            console.print(f"\n{'='*50}")
            console.print(f"Tag: {tag['name']} ({tag['contact_count']} contacts)", style="bold blue")
            console.print(f"{'='*50}")
            
            # Get contacts for this tag
            contacts = self.api.get_contacts_by_tag(tag["name"])
            
            if contacts:
                # Show preview (first 3 contacts)
                preview_contacts = contacts[:3]
                console.print(f"Preview (showing {len(preview_contacts)} of {len(contacts)} contacts):", style="cyan")
                
                for contact in preview_contacts:
                    console.print(f"  • {contact['name']}", style="green")
                    if contact['email']:
                        console.print(f"    Email: {contact['email']}", style="dim")
                    if contact['relationship_info']['notes']:
                        note_titles = [note['title'] for note in contact['relationship_info']['notes']]
                        console.print(f"    Notes: {', '.join(note_titles)}", style="yellow")
                
                # Offer to see all contacts
                if len(contacts) > 3:
                    if Confirm.ask(f"\nShow all {len(contacts)} contacts?"):
                        self.display_contacts(contacts, f"All contacts with tag '{tag['name']}'")
                        self.handle_contact_selection(contacts)
                else:
                    # If 3 or fewer, show them directly
                    self.display_contacts(contacts, f"Contacts with tag '{tag['name']}'")
                    self.handle_contact_selection(contacts)
            else:
                console.print("No contacts found with this tag.", style="yellow")
            
            # If multiple tags, ask if user wants to see another
            if len(tags) > 1 and tag != tags[-1]:
                if not Confirm.ask(f"\nView next tag?"):
                    break
    
    def search_notes(self):
        """Search notes and show associated contacts."""
        query = Prompt.ask("Enter note title or content to search")
        notes = self.api.search_notes(query)
        
        if not notes:
            console.print("No notes found.", style="yellow")
            return
        
        # Display notes with previews
        for note in notes:
            console.print(f"\n{'='*50}")
            console.print(f"Note: {note['title']} ({note['contact_count']} contacts)", style="bold blue")
            console.print(f"{'='*50}")
            console.print(f"Content: {note['content']}", style="cyan")
            
            # Get contacts for this note
            contacts = self.api.get_contacts_by_note(note["title"])
            
            if contacts:
                # Show preview (first 3 contacts)
                preview_contacts = contacts[:3]
                console.print(f"\nPreview (showing {len(preview_contacts)} of {len(contacts)} contacts):", style="cyan")
                
                for contact in preview_contacts:
                    console.print(f"  • {contact['name']}", style="green")
                    if contact['email']:
                        console.print(f"    Email: {contact['email']}", style="dim")
                    if contact['relationship_info']['tags']:
                        console.print(f"    Tags: {', '.join(contact['relationship_info']['tags'])}", style="yellow")
                
                # Offer to see all contacts
                if len(contacts) > 3:
                    if Confirm.ask(f"\nShow all {len(contacts)} contacts?"):
                        self.display_contacts(contacts, f"All contacts with note '{note['title']}'")
                        self.handle_contact_selection(contacts)
                else:
                    # If 3 or fewer, show them directly
                    self.display_contacts(contacts, f"Contacts with note '{note['title']}'")
                    self.handle_contact_selection(contacts)
            else:
                console.print("No contacts found with this note.", style="yellow")
            
            # If multiple notes, ask if user wants to see another
            if len(notes) > 1 and note != notes[-1]:
                if not Confirm.ask(f"\nView next note?"):
                    break
    
    def browse_all_contacts(self):
        """Browse all contacts."""
        contacts = self.api.list_all_contacts()
        if not contacts:
            console.print("No contacts found.", style="yellow")
            return
        
        self.display_contacts(contacts, "All Contacts")
        self.handle_contact_selection(contacts)
    
    def display_contacts(self, contacts: List[Dict[str, Any]], title: str):
        """Display a list of contacts in a table."""
        table = Table(title=title)
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Name", style="green")
        table.add_column("Email", style="magenta")
        table.add_column("Tags", style="yellow")
        table.add_column("Notes", style="blue")
        
        for contact in contacts:
            tags = ", ".join(contact["relationship_info"]["tags"]) if contact["relationship_info"]["tags"] else "None"
            notes = ", ".join([note["title"] for note in contact["relationship_info"]["notes"]]) if contact["relationship_info"]["notes"] else "None"
            
            table.add_row(
                str(contact["id"]),
                contact["name"],
                contact["email"] or "",
                tags,
                notes
            )
        
        console.print(table)
    
    def handle_contact_selection(self, contacts: List[Dict[str, Any]]):
        """Handle contact selection and show contact details."""
        if len(contacts) == 1:
            contact_id = contacts[0]["id"]
        else:
            contact_ids = [str(contact["id"]) for contact in contacts]
            contact_id = int(Prompt.ask("Select a contact ID", choices=contact_ids))
        
        self.show_contact_details(contact_id)
    
    def show_contact_details(self, contact_id: int):
        """Show detailed information about a contact."""
        contact = self.api.get_contact_details(contact_id)
        if not contact:
            console.print("Contact not found.", style="red")
            return
        
        console.print(f"\n{'='*40}")
        console.print(f"Contact Details: {contact['name']}", style="bold blue")
        console.print(f"{'='*40}")
        console.print(f"ID: {contact['id']}")
        console.print(f"Name: {contact['name']}")
        if contact['email']:
            console.print(f"Email: {contact['email']}")
        if contact['phone']:
            console.print(f"Phone: {contact['phone']}")
        
        console.print(f"\nTags: {', '.join(contact['relationship_info']['tags']) if contact['relationship_info']['tags'] else 'None'}")
        console.print(f"Notes:")
        for note in contact['relationship_info']['notes']:
            console.print(f"  - {note['title']}: {note['content']}")
        
        self.contact_actions_menu(contact_id)
    
    def contact_actions_menu(self, contact_id: int):
        """Show actions available for a contact."""
        while True:
            console.print(f"\n{'='*30}")
            console.print("Contact Actions", style="bold blue")
            console.print(f"{'='*30}")
            console.print("1. Add tag")
            console.print("2. Remove tag")
            console.print("3. Add note")
            console.print("4. Remove note")
            console.print("5. Back to search")
            console.print()
            
            choice = Prompt.ask("Select an action", choices=["1", "2", "3", "4", "5"])
            
            if choice == "1":
                self.add_tag_to_contact(contact_id)
            elif choice == "2":
                self.remove_tag_from_contact(contact_id)
            elif choice == "3":
                self.add_note_to_contact(contact_id)
            elif choice == "4":
                self.remove_note_from_contact(contact_id)
            elif choice == "5":
                break
    
    def add_tag_to_contact(self, contact_id: int):
        """Add a tag to a contact."""
        tag_name = Prompt.ask("Enter tag name")
        if self.api.add_tag_to_contact(contact_id, tag_name):
            console.print(f"Added tag '{tag_name}' to contact.", style="green")
        else:
            console.print("Failed to add tag.", style="red")
    
    def remove_tag_from_contact(self, contact_id: int):
        """Remove a tag from a contact."""
        contact = self.api.get_contact_details(contact_id)
        if not contact or not contact['relationship_info']['tags']:
            console.print("No tags to remove.", style="yellow")
            return
        
        tag_name = Prompt.ask("Select tag to remove", choices=contact['relationship_info']['tags'])
        if self.api.remove_tag_from_contact(contact_id, tag_name):
            console.print(f"Removed tag '{tag_name}' from contact.", style="green")
        else:
            console.print("Failed to remove tag.", style="red")
    
    def add_note_to_contact(self, contact_id: int):
        """Add a note to a contact."""
        note_title = Prompt.ask("Enter note title")
        note_content = Prompt.ask("Enter note content")
        if self.api.add_note_to_contact(contact_id, note_title, note_content):
            console.print(f"Added note '{note_title}' to contact.", style="green")
        else:
            console.print("Failed to add note.", style="red")
    
    def remove_note_from_contact(self, contact_id: int):
        """Remove a note from a contact."""
        contact = self.api.get_contact_details(contact_id)
        if not contact or not contact['relationship_info']['notes']:
            console.print("No notes to remove.", style="yellow")
            return
        
        note_titles = [note['title'] for note in contact['relationship_info']['notes']]
        note_title = Prompt.ask("Select note to remove", choices=note_titles)
        if self.api.remove_note_from_contact(contact_id, note_title):
            console.print(f"Removed note '{note_title}' from contact.", style="green")
        else:
            console.print("Failed to remove note.", style="red")
    
    def manage_tags_notes_menu(self):
        """Manage tags and notes menu."""
        while True:
            console.print("\n" + "-"*30)
            console.print("Manage Tags & Notes", style="bold blue")
            console.print("-"*30)
            console.print()
            console.print("1. List all tags")
            console.print("2. Create tag")
            console.print("3. Delete tag")
            console.print("4. List all notes")
            console.print("5. Create note")
            console.print("6. Update note")
            console.print("7. Delete note")
            console.print("8. Back to main menu")
            console.print()
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
            
            if choice == "1":
                self.list_all_tags()
            elif choice == "2":
                self.create_tag()
            elif choice == "3":
                self.delete_tag()
            elif choice == "4":
                self.list_all_notes()
            elif choice == "5":
                self.create_note()
            elif choice == "6":
                self.update_note()
            elif choice == "7":
                self.delete_note()
            elif choice == "8":
                break
    
    def list_all_tags(self):
        """List all tags."""
        tags = self.api.list_all_tags()
        if not tags:
            console.print("No tags found.", style="yellow")
            return
        
        table = Table(title="All Tags")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Name", style="green")
        table.add_column("Contact Count", style="magenta", justify="right")
        
        for tag in tags:
            table.add_row(str(tag["id"]), tag["name"], str(tag["contact_count"]))
        
        console.print(table)
    
    def create_tag(self):
        """Create a new tag."""
        tag_name = Prompt.ask("Enter tag name")
        tag = self.api.create_tag(tag_name)
        if tag:
            console.print(f"Created tag '{tag_name}'.", style="green")
        else:
            console.print(f"Tag '{tag_name}' already exists.", style="yellow")
    
    def delete_tag(self):
        """Delete a tag."""
        tags = self.api.list_all_tags()
        if not tags:
            console.print("No tags to delete.", style="yellow")
            return
        
        tag_names = [tag["name"] for tag in tags]
        tag_name = Prompt.ask("Select tag to delete", choices=tag_names)
        
        if Confirm.ask(f"Are you sure you want to delete tag '{tag_name}'?"):
            if self.api.delete_tag(tag_name):
                console.print(f"Deleted tag '{tag_name}'.", style="green")
            else:
                console.print("Failed to delete tag.", style="red")
    
    def list_all_notes(self):
        """List all notes."""
        notes = self.api.list_all_notes()
        if not notes:
            console.print("No notes found.", style="yellow")
            return
        
        table = Table(title="All Notes")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Title", style="green")
        table.add_column("Content", style="yellow")
        table.add_column("Contact Count", style="magenta", justify="right")
        
        for note in notes:
            content_preview = note["content"][:50] + "..." if len(note["content"]) > 50 else note["content"]
            table.add_row(str(note["id"]), note["title"], content_preview, str(note["contact_count"]))
        
        console.print(table)
    
    def create_note(self):
        """Create a new note."""
        note_title = Prompt.ask("Enter note title")
        note_content = Prompt.ask("Enter note content")
        note = self.api.create_note(note_title, note_content)
        if note:
            console.print(f"Created note '{note_title}'.", style="green")
        else:
            console.print(f"Note '{note_title}' already exists.", style="yellow")
    
    def update_note(self):
        """Update an existing note."""
        notes = self.api.list_all_notes()
        if not notes:
            console.print("No notes to update.", style="yellow")
            return
        
        note_titles = [note["title"] for note in notes]
        note_title = Prompt.ask("Select note to update", choices=note_titles)
        note_content = Prompt.ask("Enter new note content")
        
        if self.api.update_note(note_title, note_content):
            console.print(f"Updated note '{note_title}'.", style="green")
        else:
            console.print("Failed to update note.", style="red")
    
    def delete_note(self):
        """Delete a note."""
        notes = self.api.list_all_notes()
        if not notes:
            console.print("No notes to delete.", style="yellow")
            return
        
        note_titles = [note["title"] for note in notes]
        note_title = Prompt.ask("Select note to delete", choices=note_titles)
        
        if Confirm.ask(f"Are you sure you want to delete note '{note_title}'?"):
            if self.api.delete_note(note_title):
                console.print(f"Deleted note '{note_title}'.", style="green")
            else:
                console.print("Failed to delete note.", style="red")
    
    def enter_chat_mode(self):
        """Enter AI chat mode (placeholder for future implementation)."""
        console.print("\nChat mode is not yet implemented.", style="yellow")
        console.print("This will be available in a future version.", style="cyan")


def run_cli():
    """Run the PRT CLI."""
    cli = PRTCLI()
    cli.show_main_menu()


if __name__ == "__main__":
    run_cli()
