"""Test Relationship Management UI for the Textual TUI.

Lightweight TDD for relationship management functionality.
"""

from prt_src.tui.widgets.relationship import RelationshipEditor
from prt_src.tui.widgets.relationship import RelationshipGraph
from prt_src.tui.widgets.relationship import RelationshipList


class TestRelationshipEditor:
    """Test the RelationshipEditor widget."""

    def test_relationship_editor_creation(self):
        """Test that RelationshipEditor can be created."""
        editor = RelationshipEditor()
        assert editor is not None
        assert hasattr(editor, "relationship")

    def test_relationship_editor_set_relationship(self):
        """Test setting a relationship to edit."""
        relationship = {
            "from_contact": "Alice",
            "to_contact": "Bob",
            "type": "friend",
            "strength": 5,
        }

        editor = RelationshipEditor()
        editor.set_relationship(relationship)

        assert editor.relationship == relationship
        assert editor.get_field("type") == "friend"
        assert editor.get_field("strength") == 5

    def test_relationship_editor_validation(self):
        """Test relationship validation."""
        editor = RelationshipEditor()

        # Invalid - missing required fields
        invalid_rel = {"from_contact": "Alice"}
        assert not editor.validate_relationship(invalid_rel)

        # Valid relationship
        valid_rel = {"from_contact": "Alice", "to_contact": "Bob", "type": "friend"}
        assert editor.validate_relationship(valid_rel)

    def test_relationship_editor_save(self):
        """Test saving relationship."""
        save_called = False
        saved_rel = None

        def on_save(rel):
            nonlocal save_called, saved_rel
            save_called = True
            saved_rel = rel

        editor = RelationshipEditor(on_save=on_save)
        relationship = {"from_contact": "Alice", "to_contact": "Bob", "type": "colleague"}

        editor.set_relationship(relationship)
        editor.save()

        assert save_called
        assert saved_rel["type"] == "colleague"


class TestRelationshipList:
    """Test the RelationshipList widget."""

    def test_relationship_list_creation(self):
        """Test that RelationshipList can be created."""
        rel_list = RelationshipList()
        assert rel_list is not None
        assert hasattr(rel_list, "relationships")

    def test_relationship_list_load(self):
        """Test loading relationships."""
        relationships = [
            {"from_contact": "Alice", "to_contact": "Bob", "type": "friend"},
            {"from_contact": "Bob", "to_contact": "Charlie", "type": "colleague"},
            {"from_contact": "Alice", "to_contact": "Charlie", "type": "family"},
        ]

        rel_list = RelationshipList()
        rel_list.load_relationships(relationships)

        assert len(rel_list.relationships) == 3
        assert rel_list.relationships[0]["from_contact"] == "Alice"

    def test_relationship_list_filter_by_contact(self):
        """Test filtering relationships by contact."""
        relationships = [
            {"from_contact": "Alice", "to_contact": "Bob", "type": "friend"},
            {"from_contact": "Bob", "to_contact": "Charlie", "type": "colleague"},
            {"from_contact": "Alice", "to_contact": "Charlie", "type": "family"},
        ]

        rel_list = RelationshipList()
        rel_list.load_relationships(relationships)

        # Filter by Alice
        rel_list.filter_by_contact("Alice")
        assert len(rel_list.filtered_relationships) == 2

    def test_relationship_list_group_by_type(self):
        """Test grouping relationships by type."""
        relationships = [
            {"from_contact": "Alice", "to_contact": "Bob", "type": "friend"},
            {"from_contact": "Bob", "to_contact": "Charlie", "type": "friend"},
            {"from_contact": "Alice", "to_contact": "David", "type": "family"},
        ]

        rel_list = RelationshipList()
        rel_list.load_relationships(relationships)

        grouped = rel_list.group_by_type()
        assert len(grouped["friend"]) == 2
        assert len(grouped["family"]) == 1


class TestRelationshipGraph:
    """Test the RelationshipGraph widget."""

    def test_relationship_graph_creation(self):
        """Test that RelationshipGraph can be created."""
        graph = RelationshipGraph()
        assert graph is not None
        assert hasattr(graph, "nodes")
        assert hasattr(graph, "edges")

    def test_relationship_graph_add_nodes(self):
        """Test adding nodes to the graph."""
        graph = RelationshipGraph()

        graph.add_node("Alice")
        graph.add_node("Bob")

        assert "Alice" in graph.nodes
        assert "Bob" in graph.nodes
        assert len(graph.nodes) == 2

    def test_relationship_graph_add_edges(self):
        """Test adding edges to the graph."""
        graph = RelationshipGraph()

        graph.add_node("Alice")
        graph.add_node("Bob")
        graph.add_edge("Alice", "Bob", "friend")

        assert len(graph.edges) == 1
        assert graph.edges[0]["from"] == "Alice"
        assert graph.edges[0]["to"] == "Bob"
        assert graph.edges[0]["type"] == "friend"

    def test_relationship_graph_from_relationships(self):
        """Test building graph from relationships."""
        relationships = [
            {"from_contact": "Alice", "to_contact": "Bob", "type": "friend"},
            {"from_contact": "Bob", "to_contact": "Charlie", "type": "colleague"},
            {"from_contact": "Alice", "to_contact": "Charlie", "type": "family"},
        ]

        graph = RelationshipGraph()
        graph.from_relationships(relationships)

        assert len(graph.nodes) == 3
        assert len(graph.edges) == 3
        assert "Alice" in graph.nodes
        assert "Bob" in graph.nodes
        assert "Charlie" in graph.nodes
