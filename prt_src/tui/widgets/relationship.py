"""Relationship Management UI widgets for the PRT Textual TUI.

Provides widgets for viewing, editing, and visualizing relationships
between contacts.
"""

from collections.abc import Callable

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.widgets import Button
from textual.widgets import Input
from textual.widgets import Label
from textual.widgets import Select
from textual.widgets import Static

from prt_src.tui.widgets.base import ModeAwareWidget


class RelationshipEditor(Static):
    """Editor for creating and modifying relationships."""

    def __init__(self, on_save: Callable | None = None):
        """Initialize the relationship editor.

        Args:
            on_save: Callback when relationship is saved
        """
        super().__init__()
        self.relationship: dict | None = None
        self.on_save = on_save
        self.add_class("relationship-editor")

    def compose(self) -> ComposeResult:
        """Compose the relationship editor layout."""
        with Vertical(classes="editor-container"):
            yield Label("Relationship Editor", classes="editor-title")

            # From contact field
            yield Label("From Contact:", classes="field-label")
            yield Input(id="from-contact", placeholder="Contact name", classes="field-input")

            # To contact field
            yield Label("To Contact:", classes="field-label")
            yield Input(id="to-contact", placeholder="Contact name", classes="field-input")

            # Relationship type
            yield Label("Type:", classes="field-label")
            yield Select(
                [
                    ("friend", "Friend"),
                    ("family", "Family"),
                    ("colleague", "Colleague"),
                    ("acquaintance", "Acquaintance"),
                ],
                id="rel-type",
                classes="field-select",
            )

            # Strength (1-10)
            yield Label("Strength (1-10):", classes="field-label")
            yield Input(id="strength", placeholder="5", classes="field-input")

            # Action buttons
            with Horizontal(classes="button-row"):
                yield Button("Save", id="save-rel", classes="action-button")
                yield Button("Cancel", id="cancel-rel", classes="action-button")

    def set_relationship(self, relationship: dict) -> None:
        """Set the relationship to edit.

        Args:
            relationship: Relationship dictionary
        """
        self.relationship = relationship.copy()

        # Update fields
        try:
            self.query_one("#from-contact", Input).value = relationship.get("from_contact", "")
            self.query_one("#to-contact", Input).value = relationship.get("to_contact", "")

            rel_type = relationship.get("type", "friend")
            self.query_one("#rel-type", Select).value = rel_type

            strength = str(relationship.get("strength", 5))
            self.query_one("#strength", Input).value = strength
        except Exception:
            pass

    def get_field(self, field_name: str):
        """Get the value of a field.

        Args:
            field_name: Name of the field

        Returns:
            Field value
        """
        if self.relationship:
            return self.relationship.get(field_name)
        return None

    def validate_relationship(self, relationship: dict) -> bool:
        """Validate a relationship has required fields.

        Args:
            relationship: Relationship to validate

        Returns:
            True if valid
        """
        required = ["from_contact", "to_contact", "type"]
        return all(field in relationship for field in required)

    def validate_strength(self, value: str) -> bool:
        """Validate strength is between 1-10.

        Args:
            value: The strength value to validate

        Returns:
            True if valid
        """
        try:
            strength = int(value)
            return 1 <= strength <= 10
        except (ValueError, TypeError):
            return False

    @on(Button.Pressed, "#save-rel")
    def handle_save(self) -> None:
        """Handle save button click."""
        try:
            # Gather current form data
            from_contact = self.query_one("#from-contact", Input).value
            to_contact = self.query_one("#to-contact", Input).value
            rel_type = self.query_one("#rel-type", Select).value
            strength_str = self.query_one("#strength", Input).value

            # Validate and convert strength
            strength = 5  # default
            if strength_str and self.validate_strength(strength_str):
                strength = int(strength_str)

            # Create relationship object with consistent schema
            self.relationship = {
                "from_contact": from_contact,
                "to_contact": to_contact,
                "type": rel_type or "friend",
                "strength": strength,
            }

            if self.validate_relationship(self.relationship) and self.on_save:
                self.on_save(self.relationship)
        except Exception:
            pass

    @on(Button.Pressed, "#cancel-rel")
    def handle_cancel(self) -> None:
        """Handle cancel button click."""
        # Reset form to original values if editing
        if self.relationship:
            self.set_relationship(self.relationship)

    def save(self) -> None:
        """Save the current relationship."""
        if self.relationship and self.validate_relationship(self.relationship) and self.on_save:
            self.on_save(self.relationship)


class RelationshipList(ModeAwareWidget):
    """List view for relationships with filtering and grouping."""

    def __init__(self):
        """Initialize the relationship list."""
        super().__init__()
        self.relationships: list[dict] = []
        self.filtered_relationships: list[dict] = []
        self.current_contact: str | None = None
        self.add_class("relationship-list")

    def compose(self) -> ComposeResult:
        """Compose the relationship list layout."""
        with Vertical(classes="list-container"):
            # Header with filter options
            with Horizontal(classes="list-header"):
                yield Label("Relationships", classes="list-title")
                yield Button("Add New", id="add-rel", classes="action-button")

            # Filter bar
            with Horizontal(classes="filter-bar"):
                yield Label("Filter by:", classes="filter-label")
                yield Input(id="contact-filter", placeholder="Contact name", classes="filter-input")
                yield Button("Apply", id="apply-filter", classes="filter-button")
                yield Button("Clear", id="clear-filter", classes="filter-button")

            # Relationships container
            yield Vertical(id="relationships-container", classes="relationships-container")

    @on(Button.Pressed, "#apply-filter")
    def handle_apply_filter(self) -> None:
        """Handle apply filter button click."""
        try:
            contact_name = self.query_one("#contact-filter", Input).value
            if contact_name:
                self.filter_by_contact(contact_name)
        except Exception:
            pass

    @on(Button.Pressed, "#clear-filter")
    def handle_clear_filter(self) -> None:
        """Handle clear filter button click."""
        try:
            self.query_one("#contact-filter", Input).value = ""
            self.filtered_relationships = self.relationships.copy()
            self.current_contact = None
            self._update_display()
        except Exception:
            pass

    @on(Button.Pressed, "#add-rel")
    def handle_add_relationship(self) -> None:
        """Handle add new relationship button."""
        # This would typically open a dialog or switch to edit mode
        # For now, just a placeholder

    def load_relationships(self, relationships: list[dict]) -> None:
        """Load relationships into the list.

        Args:
            relationships: List of relationship dictionaries
        """
        self.relationships = relationships
        self.filtered_relationships = relationships.copy()
        self._update_display()

    def filter_by_contact(self, contact_name: str) -> None:
        """Filter relationships by contact name.

        Args:
            contact_name: Name of contact to filter by
        """
        self.current_contact = contact_name
        self.filtered_relationships = [
            rel
            for rel in self.relationships
            if rel.get("from_contact") == contact_name or rel.get("to_contact") == contact_name
        ]
        self._update_display()

    def group_by_type(self) -> dict[str, list[dict]]:
        """Group relationships by type.

        Returns:
            Dictionary mapping type to list of relationships
        """
        grouped = {}
        for rel in self.filtered_relationships:
            rel_type = rel.get("type", "unknown")
            if rel_type not in grouped:
                grouped[rel_type] = []
            grouped[rel_type].append(rel)
        return grouped

    def _update_display(self) -> None:
        """Update the relationships display."""
        try:
            container = self.query_one("#relationships-container", Vertical)
            container.remove_children()

            # Group by type for better organization
            grouped = self.group_by_type()

            for rel_type, rels in grouped.items():
                # Type header
                container.mount(Label(f"{rel_type.title()} ({len(rels)})", classes="type-header"))

                # Relationships of this type
                for rel in rels:
                    from_contact = rel.get("from_contact", "Unknown")
                    to_contact = rel.get("to_contact", "Unknown")
                    strength = rel.get("strength", "")

                    rel_text = f"{from_contact} → {to_contact}"
                    if strength:
                        rel_text += f" (strength: {strength})"

                    container.mount(Static(rel_text, classes="relationship-item"))
        except Exception:
            pass


class RelationshipGraph(Static):
    """Visual graph representation of relationships."""

    def __init__(self):
        """Initialize the relationship graph."""
        super().__init__()
        self.nodes: set[str] = set()
        self.edges: list[dict] = []
        self.add_class("relationship-graph")

    def compose(self) -> ComposeResult:
        """Compose the graph layout."""
        with Vertical(classes="graph-container"):
            yield Label("Relationship Graph", classes="graph-title")
            yield Static("", id="graph-display", classes="graph-display")

            # Graph stats
            yield Static("", id="graph-stats", classes="graph-stats")

    def add_node(self, node: str) -> None:
        """Add a node to the graph.

        Args:
            node: Node name (contact name)
        """
        self.nodes.add(node)
        self._update_display()

    def add_edge(self, from_node: str, to_node: str, edge_type: str) -> None:
        """Add an edge between nodes.

        Args:
            from_node: Source node
            to_node: Target node
            edge_type: Type of relationship
        """
        self.nodes.add(from_node)
        self.nodes.add(to_node)
        self.edges.append({"from": from_node, "to": to_node, "type": edge_type})
        self._update_display()

    def from_relationships(self, relationships: list[dict]) -> None:
        """Build graph from list of relationships.

        Args:
            relationships: List of relationship dictionaries
        """
        self.nodes.clear()
        self.edges.clear()

        for rel in relationships:
            from_contact = rel.get("from_contact")
            to_contact = rel.get("to_contact")
            rel_type = rel.get("type", "unknown")

            if from_contact and to_contact:
                self.add_edge(from_contact, to_contact, rel_type)

    def _update_display(self) -> None:
        """Update the graph display."""
        try:
            display = self.query_one("#graph-display", Static)
            stats = self.query_one("#graph-stats", Static)

            # Simple ASCII representation
            graph_text = "Graph Visualization:\n\n"

            # Show nodes
            graph_text += f"Nodes ({len(self.nodes)}):\n"
            for node in sorted(self.nodes):
                graph_text += f"  • {node}\n"

            # Show edges
            graph_text += f"\nConnections ({len(self.edges)}):\n"
            for edge in self.edges:
                graph_text += f"  {edge['from']} —[{edge['type']}]→ {edge['to']}\n"

            display.update(graph_text)

            # Update stats
            stats_text = f"Total Nodes: {len(self.nodes)} | Total Edges: {len(self.edges)}"
            stats.update(stats_text)

        except Exception:
            pass
