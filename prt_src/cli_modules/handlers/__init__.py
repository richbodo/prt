"""
Domain handlers for PRT CLI.

This module contains domain-specific handler functions for managing different
aspects of the PRT system (contacts, relationships, tags, notes, etc.).
"""

from .contacts import handle_contact_search_results
from .contacts import handle_contacts_view
from .database import handle_database_backup
from .database import handle_database_menu
from .database import handle_database_stats
from .database import handle_database_status
from .database import handle_database_test
from .menu import show_main_menu
from .notes import handle_create_note
from .notes import handle_delete_note
from .notes import handle_edit_note
from .notes import handle_note_search_results
from .notes import handle_notes_menu
from .notes import handle_view_notes
from .relationships import handle_add_relationship
from .relationships import handle_bulk_relationships
from .relationships import handle_delete_relationship
from .relationships import handle_export_relationships
from .relationships import handle_find_connection_path
from .relationships import handle_find_mutual_connections
from .relationships import handle_list_relationship_types
from .relationships import handle_relationship_analytics
from .relationships import handle_relationships_menu
from .relationships import handle_view_relationships
from .search import handle_search_menu
from .tags import handle_create_tag
from .tags import handle_delete_tag
from .tags import handle_tag_search_results
from .tags import handle_tags_menu
from .tags import handle_view_tags

__all__ = [
    # Menu
    "show_main_menu",
    # Contacts
    "handle_contacts_view",
    "handle_contact_search_results",
    # Tags
    "handle_view_tags",
    "handle_tags_menu",
    "handle_create_tag",
    "handle_delete_tag",
    "handle_tag_search_results",
    # Notes
    "handle_view_notes",
    "handle_notes_menu",
    "handle_create_note",
    "handle_edit_note",
    "handle_delete_note",
    "handle_note_search_results",
    # Relationships
    "handle_relationships_menu",
    "handle_view_relationships",
    "handle_add_relationship",
    "handle_list_relationship_types",
    "handle_delete_relationship",
    "handle_relationship_analytics",
    "handle_find_mutual_connections",
    "handle_find_connection_path",
    "handle_export_relationships",
    "handle_bulk_relationships",
    # Database
    "handle_database_status",
    "handle_database_backup",
    "handle_database_menu",
    "handle_database_test",
    "handle_database_stats",
    # Search
    "handle_search_menu",
]
