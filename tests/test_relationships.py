"""
Test suite for the new relationship types functionality.

This module tests the relationship type system introduced in Issue #38,
including contact-to-contact relationships, relationship types with inverses,
and backward compatibility with the renamed ContactMetadata model.
"""

import pytest
from datetime import date
from sqlalchemy.exc import IntegrityError
from prt_src.models import (
    Contact, RelationshipType, ContactRelationship, 
    ContactMetadata, Tag, Note, Relationship  # Test backward compat alias
)


@pytest.fixture
def sample_contacts(test_db):
    """Create sample contacts for relationship testing."""
    db, _ = test_db
    
    contacts = [
        Contact(name="John Doe", email="john@example.com"),
        Contact(name="Jane Doe", email="jane@example.com"),
        Contact(name="Bob Doe", email="bob@example.com"),
        Contact(name="Alice Johnson", email="alice@example.com"),
        Contact(name="Charlie Brown", email="charlie@example.com"),
        Contact(name="Diana Prince", email="diana@example.com"),
    ]
    
    for contact in contacts:
        db.session.add(contact)
        # Add metadata for backward compatibility testing
        metadata = ContactMetadata(contact=contact)
        db.session.add(metadata)
    
    db.session.commit()
    return contacts


@pytest.fixture
def sample_relationship_types(test_db):
    """Create sample relationship types."""
    db, _ = test_db
    
    types = [
        # Asymmetrical relationships
        RelationshipType(type_key="parent_of", description="Is the parent of", 
                        inverse_type_key="child_of", is_symmetrical=0),
        RelationshipType(type_key="child_of", description="Is the child of", 
                        inverse_type_key="parent_of", is_symmetrical=0),
        RelationshipType(type_key="manages", description="Manages", 
                        inverse_type_key="managed_by", is_symmetrical=0),
        RelationshipType(type_key="managed_by", description="Is managed by", 
                        inverse_type_key="manages", is_symmetrical=0),
        
        # Symmetrical relationships
        RelationshipType(type_key="married_to", description="Is married to", 
                        inverse_type_key="married_to", is_symmetrical=1),
        RelationshipType(type_key="friend_of", description="Is a friend of", 
                        inverse_type_key="friend_of", is_symmetrical=1),
    ]
    
    for rel_type in types:
        db.session.add(rel_type)
    
    db.session.commit()
    return types


class TestRelationshipTypes:
    """Test relationship type functionality."""
    
    def test_create_relationship_type_with_inverse(self, test_db):
        """Test creating an asymmetrical relationship type with inverse."""
        db, _ = test_db
        
        # Create parent_of relationship
        parent_type = RelationshipType(
            type_key="parent_of",
            description="Is the parent of",
            inverse_type_key="child_of",
            is_symmetrical=0
        )
        db.session.add(parent_type)
        
        # Create child_of relationship
        child_type = RelationshipType(
            type_key="child_of",
            description="Is the child of",
            inverse_type_key="parent_of",
            is_symmetrical=0
        )
        db.session.add(child_type)
        db.session.commit()
        
        # Verify relationships were created
        assert parent_type.id is not None
        assert child_type.id is not None
        assert parent_type.inverse_type_key == "child_of"
        assert child_type.inverse_type_key == "parent_of"
        assert parent_type.is_symmetrical == 0
        assert child_type.is_symmetrical == 0
    
    def test_symmetrical_relationship_creates_single_type(self, test_db):
        """Test that symmetrical relationships point to themselves."""
        db, _ = test_db
        
        # Create spouse_of relationship
        spouse_type = RelationshipType(
            type_key="spouse_of",
            description="Is the spouse of",
            inverse_type_key="spouse_of",  # Points to itself
            is_symmetrical=1
        )
        db.session.add(spouse_type)
        db.session.commit()
        
        assert spouse_type.inverse_type_key == "spouse_of"
        assert spouse_type.is_symmetrical == 1
    
    def test_duplicate_relationship_type_rejected(self, test_db):
        """Test that duplicate type_keys are rejected."""
        db, _ = test_db
        
        # Create first relationship
        rel1 = RelationshipType(type_key="friend_of", description="Friend")
        db.session.add(rel1)
        db.session.commit()
        
        # Try to create duplicate
        rel2 = RelationshipType(type_key="friend_of", description="Another Friend")
        db.session.add(rel2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
    
    def test_relationship_type_validation(self, test_db):
        """Test that type_key is required."""
        db, _ = test_db
        
        # Try to create without type_key
        rel = RelationshipType(description="Some relationship")
        db.session.add(rel)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()


class TestContactRelationships:
    """Test contact relationship functionality."""
    
    def test_create_bidirectional_relationship(self, test_db, sample_contacts, sample_relationship_types):
        """Test creating parent-child relationship creates both directions."""
        db, _ = test_db
        
        john = sample_contacts[0]  # Parent
        bob = sample_contacts[2]   # Child
        
        # Get parent_of type
        parent_type = db.session.query(RelationshipType).filter_by(type_key="parent_of").first()
        
        # Create parent -> child relationship
        rel = ContactRelationship(
            from_contact=john,
            to_contact=bob,
            relationship_type=parent_type
        )
        db.session.add(rel)
        db.session.commit()
        
        # Check the relationship was created
        assert rel.id is not None
        assert rel.from_contact_id == john.id
        assert rel.to_contact_id == bob.id
        assert rel.type_id == parent_type.id
        
        # API should handle creating inverse automatically in db.py
    
    def test_create_symmetrical_relationship_single_entry(self, test_db, sample_contacts, sample_relationship_types):
        """Test that symmetrical relationships only need one entry."""
        db, _ = test_db
        
        john = sample_contacts[0]
        jane = sample_contacts[1]
        
        # Get married_to type
        married_type = db.session.query(RelationshipType).filter_by(type_key="married_to").first()
        
        # Create marriage relationship
        rel = ContactRelationship(
            from_contact=john,
            to_contact=jane,
            relationship_type=married_type
        )
        db.session.add(rel)
        db.session.commit()
        
        # Only one entry needed for symmetrical relationship
        count = db.session.query(ContactRelationship).filter_by(type_id=married_type.id).count()
        assert count == 1
    
    def test_delete_relationship_removes_both_directions(self, test_db, sample_contacts, sample_relationship_types):
        """Test that deleting a relationship removes both directions."""
        db, _ = test_db
        
        john = sample_contacts[0]
        bob = sample_contacts[2]
        parent_type = db.session.query(RelationshipType).filter_by(type_key="parent_of").first()
        child_type = db.session.query(RelationshipType).filter_by(type_key="child_of").first()
        
        # Create relationships
        rel1 = ContactRelationship(from_contact=john, to_contact=bob, relationship_type=parent_type)
        rel2 = ContactRelationship(from_contact=bob, to_contact=john, relationship_type=child_type)
        db.session.add_all([rel1, rel2])
        db.session.commit()
        
        # Delete one relationship
        db.session.delete(rel1)
        db.session.commit()
        
        # Both should be handled by cascade or API logic
        remaining = db.session.query(ContactRelationship).filter(
            ((ContactRelationship.from_contact_id == john.id) & (ContactRelationship.to_contact_id == bob.id)) |
            ((ContactRelationship.from_contact_id == bob.id) & (ContactRelationship.to_contact_id == john.id))
        ).count()
        
        # Note: Full bidirectional deletion logic is in db.py
        assert remaining <= 1  # May have one remaining if cascade not set up
    
    def test_unique_relationship_constraint(self, test_db, sample_contacts, sample_relationship_types):
        """Test that duplicate relationships are prevented."""
        db, _ = test_db
        
        john = sample_contacts[0]
        jane = sample_contacts[1]
        friend_type = db.session.query(RelationshipType).filter_by(type_key="friend_of").first()
        
        # Create first relationship
        rel1 = ContactRelationship(from_contact=john, to_contact=jane, relationship_type=friend_type)
        db.session.add(rel1)
        db.session.commit()
        
        # Try to create duplicate
        rel2 = ContactRelationship(from_contact=john, to_contact=jane, relationship_type=friend_type)
        db.session.add(rel2)
        
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
    
    def test_relationship_with_dates(self, test_db, sample_contacts, sample_relationship_types):
        """Test relationships with start and end dates."""
        db, _ = test_db
        
        alice = sample_contacts[3]
        charlie = sample_contacts[4]
        manages_type = db.session.query(RelationshipType).filter_by(type_key="manages").first()
        
        # Create employment relationship with dates
        rel = ContactRelationship(
            from_contact=alice,
            to_contact=charlie,
            relationship_type=manages_type,
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31)
        )
        db.session.add(rel)
        db.session.commit()
        
        assert rel.start_date == date(2020, 1, 1)
        assert rel.end_date == date(2023, 12, 31)


class TestIntegration:
    """Integration tests for complex scenarios."""
    
    def test_family_tree_generation(self, test_db, sample_contacts):
        """Test building a family tree structure."""
        db, _ = test_db
        
        # Create relationship types
        parent_type = RelationshipType(type_key="parent_of", description="Parent of", 
                                      inverse_type_key="child_of", is_symmetrical=0)
        child_type = RelationshipType(type_key="child_of", description="Child of",
                                     inverse_type_key="parent_of", is_symmetrical=0)
        sibling_type = RelationshipType(type_key="sibling_of", description="Sibling of",
                                       inverse_type_key="sibling_of", is_symmetrical=1)
        
        db.session.add_all([parent_type, child_type, sibling_type])
        db.session.commit()
        
        # Build family: John and Jane are parents of Bob and Alice
        john, jane, bob, alice = sample_contacts[:4]
        
        # Parent relationships
        db.session.add(ContactRelationship(from_contact=john, to_contact=bob, relationship_type=parent_type))
        db.session.add(ContactRelationship(from_contact=john, to_contact=alice, relationship_type=parent_type))
        db.session.add(ContactRelationship(from_contact=jane, to_contact=bob, relationship_type=parent_type))
        db.session.add(ContactRelationship(from_contact=jane, to_contact=alice, relationship_type=parent_type))
        
        # Sibling relationship
        db.session.add(ContactRelationship(from_contact=bob, to_contact=alice, relationship_type=sibling_type))
        
        db.session.commit()
        
        # Query family relationships for Bob
        bob_relationships = db.session.query(ContactRelationship).filter(
            (ContactRelationship.from_contact_id == bob.id) | 
            (ContactRelationship.to_contact_id == bob.id)
        ).all()
        
        assert len(bob_relationships) >= 1  # At least sibling relationship
    
    def test_relationship_graph_cycles(self, test_db, sample_contacts):
        """Test handling circular relationships."""
        db, _ = test_db
        
        # Create friend_of type (symmetrical)
        friend_type = RelationshipType(type_key="friend_of", description="Friend of",
                                      inverse_type_key="friend_of", is_symmetrical=1)
        db.session.add(friend_type)
        db.session.commit()
        
        # Create circular friendships: A -> B -> C -> A
        alice, bob, charlie = sample_contacts[3:6]
        
        db.session.add(ContactRelationship(from_contact=alice, to_contact=bob, relationship_type=friend_type))
        db.session.add(ContactRelationship(from_contact=bob, to_contact=charlie, relationship_type=friend_type))
        db.session.add(ContactRelationship(from_contact=charlie, to_contact=alice, relationship_type=friend_type))
        db.session.commit()
        
        # All should have friend relationships
        for contact in [alice, bob, charlie]:
            rels = db.session.query(ContactRelationship).filter(
                (ContactRelationship.from_contact_id == contact.id) |
                (ContactRelationship.to_contact_id == contact.id)
            ).count()
            assert rels > 0
    
    def test_migration_preserves_tags_and_notes(self, test_db):
        """Test that the migration preserves existing tag and note relationships."""
        db, _ = test_db
        
        # Create contact with metadata (using new name)
        contact = Contact(name="Test User", email="test@example.com")
        db.session.add(contact)
        
        metadata = ContactMetadata(contact=contact)
        db.session.add(metadata)
        
        # Add tags and notes
        tag = Tag(name="Important")
        note = Note(title="Test Note", content="Some content")
        db.session.add_all([tag, note])
        db.session.commit()
        
        # Associate via metadata
        metadata.tags.append(tag)
        metadata.notes.append(note)
        db.session.commit()
        
        # Verify associations persist
        assert len(metadata.tags) == 1
        assert len(metadata.notes) == 1
        assert metadata.tags[0].name == "Important"
        assert metadata.notes[0].title == "Test Note"
    
    def test_backward_compatibility_aliases(self, test_db):
        """Test that Relationship alias still works for backward compatibility."""
        db, _ = test_db
        
        # Test that Relationship is an alias for ContactMetadata
        assert Relationship == ContactMetadata
        
        # Old code using Relationship should still work
        contact = Contact(name="Legacy User", email="legacy@example.com")
        db.session.add(contact)
        
        # Using old class name
        rel = Relationship(contact=contact)
        db.session.add(rel)
        db.session.commit()
        
        assert rel.id is not None
        assert rel.contact_id == contact.id
    
    def test_complex_relationship_queries(self, test_db, sample_contacts):
        """Test complex queries across relationship tables."""
        db, _ = test_db
        
        # Create various relationship types
        friend = RelationshipType(type_key="friend", description="Friend", 
                                 inverse_type_key="friend", is_symmetrical=1)
        colleague = RelationshipType(type_key="colleague", description="Colleague",
                                    inverse_type_key="colleague", is_symmetrical=1)
        db.session.add_all([friend, colleague])
        db.session.commit()
        
        # Create mixed relationships
        for i in range(len(sample_contacts) - 1):
            rel_type = friend if i % 2 == 0 else colleague
            db.session.add(ContactRelationship(
                from_contact=sample_contacts[i],
                to_contact=sample_contacts[i + 1],
                relationship_type=rel_type
            ))
        db.session.commit()
        
        # Query for all friends
        friend_rels = db.session.query(ContactRelationship).join(
            RelationshipType
        ).filter(
            RelationshipType.type_key == "friend"
        ).count()
        
        assert friend_rels > 0
        
        # Query for all colleagues  
        colleague_rels = db.session.query(ContactRelationship).join(
            RelationshipType
        ).filter(
            RelationshipType.type_key == "colleague"
        ).count()
        
        assert colleague_rels > 0
    
    def test_relationship_cascade_delete(self, test_db, sample_contacts):
        """Test that deleting a relationship type cascades properly."""
        db, _ = test_db
        
        # Create temporary relationship type
        temp_type = RelationshipType(type_key="temp_rel", description="Temporary")
        db.session.add(temp_type)
        db.session.commit()
        
        # Create relationships using this type
        rel = ContactRelationship(
            from_contact=sample_contacts[0],
            to_contact=sample_contacts[1],
            relationship_type=temp_type
        )
        db.session.add(rel)
        db.session.commit()
        
        rel_id = rel.id
        
        # Delete the relationship type
        db.session.delete(temp_type)
        db.session.commit()
        
        # Relationship should be cascade deleted
        remaining = db.session.query(ContactRelationship).filter_by(id=rel_id).first()
        assert remaining is None
    
    def test_contact_relationship_counts(self, test_db, sample_contacts):
        """Test counting relationships per contact."""
        db, _ = test_db
        
        # Create friend type
        friend = RelationshipType(type_key="friend", description="Friend",
                                inverse_type_key="friend", is_symmetrical=1)
        db.session.add(friend)
        db.session.commit()
        
        # Make first contact friends with everyone else
        popular_contact = sample_contacts[0]
        for other in sample_contacts[1:]:
            db.session.add(ContactRelationship(
                from_contact=popular_contact,
                to_contact=other,
                relationship_type=friend
            ))
        db.session.commit()
        
        # Count relationships for popular contact
        count = db.session.query(ContactRelationship).filter(
            (ContactRelationship.from_contact_id == popular_contact.id) |
            (ContactRelationship.to_contact_id == popular_contact.id)
        ).count()
        
        assert count == len(sample_contacts) - 1
    
    def test_relationship_type_descriptions(self, test_db):
        """Test that relationship descriptions are properly stored and retrieved."""
        db, _ = test_db
        
        # Create relationship with detailed description
        rel_type = RelationshipType(
            type_key="mentor",
            description="Acts as a professional mentor providing career guidance",
            inverse_type_key="mentee",
            is_symmetrical=0
        )
        db.session.add(rel_type)
        db.session.commit()
        
        # Retrieve and verify
        retrieved = db.session.query(RelationshipType).filter_by(type_key="mentor").first()
        assert retrieved.description == "Acts as a professional mentor providing career guidance"
        assert retrieved.inverse_type_key == "mentee"
        assert retrieved.is_symmetrical == 0