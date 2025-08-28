#!/usr/bin/env python3
"""
Test suite for the make_directory.py tool.

Tests all features of the directory export tool including:
- JSON parsing and validation
- Profile image handling  
- HTML/JS generation
- D3.js data formatting
- Error handling
- CLI interface
"""

import json
import os
import pytest
import shutil
import tempfile
from pathlib import Path
from PIL import Image

# Add tools to path for importing
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from make_directory import DirectoryGenerator, app
from typer.testing import CliRunner


# Test fixtures - must be at module level for pytest
@pytest.fixture
def test_export_dir(tmp_path):
    """Create a test export directory with complete data."""
    export_dir = tmp_path / "test_contacts_search_20250826_123456"
    export_dir.mkdir()
    
    # Create test JSON data with comprehensive structure
    test_data = {
        "search_request": {
            "type": "contacts",
            "term": "alice",
            "executed_at": "2025-08-26T12:34:56"
        },
        "export_info": {
            "search_type": "contacts",
            "query": "alice",
            "timestamp": "20250826_123456",
            "total_results": 6
        },
        "results": [
            {
                "contact": {
                    "id": 1,
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1-555-0101",
                    "has_profile_image": True,
                    "exported_image_path": "profile_images/1.jpg",
                    "relationship_info": {
                        "tags": ["friend", "family"],
                        "notes": [
                            {
                                "title": "Birthday Party",
                                "content": "Remember to bring cake"
                            }
                        ]
                    }
                }
            },
            {
                "contact": {
                    "id": 2,
                    "name": "Jane Smith",
                    "email": "jane.smith@email.com",
                    "phone": "+1-555-0102",
                    "has_profile_image": True,
                    "exported_image_path": "profile_images/2.jpg",
                    "relationship_info": {
                        "tags": ["colleague", "mentor"],
                        "notes": []
                    }
                }
            },
            {
                "contact": {
                    "id": 3,
                    "name": "Bob Wilson",
                    "email": "bob@work.com",
                    "phone": "+1-555-0103",
                    "has_profile_image": True,
                    "exported_image_path": "profile_images/3.jpg",
                    "relationship_info": {
                        "tags": ["friend", "neighbor"],
                        "notes": [
                            {
                                "title": "Weekend BBQ",
                                "content": "Hosting BBQ this Saturday"
                            }
                        ]
                    }
                }
            },
            {
                "contact": {
                    "id": 4,
                    "name": "Alice Johnson",
                    "email": "alice.johnson@gmail.com",
                    "phone": "+1-555-0104",
                    "has_profile_image": True,
                    "exported_image_path": "profile_images/4.jpg",
                    "relationship_info": {
                        "tags": ["classmate", "friend"],
                        "notes": [
                            {
                                "title": "Study Group",
                                "content": "Meets every Tuesday at 7pm"
                            }
                        ]
                    }
                }
            },
            {
                "contact": {
                    "id": 5,
                    "name": "Charlie Brown",
                    "email": "charlie@company.org",
                    "phone": "+1-555-0105",
                    "has_profile_image": False,
                    "exported_image_path": None,
                    "relationship_info": {
                        "tags": ["client", "business_contact"],
                        "notes": []
                    }
                }
            },
            {
                "contact": {
                    "id": 6,
                    "name": "Diana Prince",
                    "email": "diana.prince@hero.com",
                    "phone": "+1-555-0106",
                    "has_profile_image": True,
                    "exported_image_path": "profile_images/6.jpg",
                    "relationship_info": {
                        "tags": ["friend", "mentor"],
                        "notes": [
                            {
                                "title": "Training Session",
                                "content": "Leadership workshop next month"
                            }
                        ]
                    }
                }
            }
        ]
    }
    
    # Write JSON file
    json_file = export_dir / "contacts_search_results.json"
    with open(json_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Create profile images directory with test images
    profile_dir = export_dir / "profile_images"
    profile_dir.mkdir()
    
    # Create test images using PIL for contacts with profile images
    colors = ['red', 'green', 'blue', 'yellow', 'purple']
    image_ids = [1, 2, 3, 4, 6]  # Contact IDs that have profile images
    
    for i, contact_id in enumerate(image_ids):
        color = colors[i % len(colors)]
        test_image = Image.new('RGB', (256, 256), color=color)
        test_image.save(profile_dir / f"{contact_id}.jpg", "JPEG")
    
    # Create README
    readme_file = export_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write("# Test Export\nTest export for directory generation.")
    
    return export_dir, test_data


@pytest.fixture  
def tags_export_dir(tmp_path):
    """Create a test tags export with multiple relationships."""
    export_dir = tmp_path / "test_tags_search_20250826_123456"
    export_dir.mkdir()
    
    test_data = {
        "search_request": {
            "type": "tags",
            "term": "friend",
            "executed_at": "2025-08-26T12:34:56"
        },
        "export_info": {
            "search_type": "tags",
            "query": "friend",
            "timestamp": "20250826_123456",
            "total_results": 1
        },
        "results": [
            {
                "tag": {
                    "id": 1,
                    "name": "friend",
                    "contact_count": 3
                },
                "associated_contacts": [
                    {
                        "id": 1,
                        "name": "Alice Johnson",
                        "email": "alice@example.com",
                        "phone": "+1-555-0101",
                        "has_profile_image": False,
                        "exported_image_path": None,
                        "relationship_info": {
                            "tags": ["friend", "coworker"],
                            "notes": []
                        }
                    },
                    {
                        "id": 2,
                        "name": "Bob Wilson", 
                        "email": "bob@example.com",
                        "phone": "+1-555-0102",
                        "has_profile_image": False,
                        "exported_image_path": None,
                        "relationship_info": {
                            "tags": ["friend", "neighbor"],
                            "notes": []
                        }
                    },
                    {
                        "id": 3,
                        "name": "Carol Davis",
                        "email": "carol@example.com", 
                        "phone": "+1-555-0103",
                        "has_profile_image": False,
                        "exported_image_path": None,
                        "relationship_info": {
                            "tags": ["friend"],
                            "notes": []
                        }
                    }
                ]
            }
        ]
    }
    
    json_file = export_dir / "tags_search_results.json"
    with open(json_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    return export_dir, test_data


@pytest.fixture
def notes_export_dir(tmp_path):
    """Create a test notes export."""
    export_dir = tmp_path / "test_notes_search_20250826_123456"
    export_dir.mkdir()
    
    test_data = {
        "search_request": {
            "type": "notes",
            "term": "meeting",
            "executed_at": "2025-08-26T12:34:56"
        },
        "export_info": {
            "search_type": "notes",
            "query": "meeting",
            "timestamp": "20250826_123456",
            "total_results": 1
        },
        "results": [
            {
                "note": {
                    "id": 1,
                    "title": "Team Meeting",
                    "content": "Discussed quarterly goals and project timelines.",
                    "contact_count": 2
                },
                "associated_contacts": [
                    {
                        "id": 1,
                        "name": "Alice Johnson",
                        "email": "alice@example.com",
                        "phone": "+1-555-0101",
                        "has_profile_image": True,
                        "exported_image_path": "profile_images/1.jpg",
                        "relationship_info": {
                            "tags": ["coworker"],
                            "notes": [
                                {
                                    "title": "Team Meeting",
                                    "content": "Discussed quarterly goals and project timelines."
                                }
                            ]
                        }
                    },
                    {
                        "id": 2,
                        "name": "Bob Wilson",
                        "email": "bob@example.com",
                        "phone": "+1-555-0102",
                        "has_profile_image": False,
                        "exported_image_path": None,
                        "relationship_info": {
                            "tags": ["coworker"],
                            "notes": [
                                {
                                    "title": "Team Meeting",
                                    "content": "Discussed quarterly goals and project timelines."
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    
    json_file = export_dir / "notes_search_results.json"
    with open(json_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Create profile images directory with test image
    profile_dir = export_dir / "profile_images"
    profile_dir.mkdir()
    test_image = Image.new('RGB', (256, 256), color='green')
    test_image.save(profile_dir / "1.jpg", "JPEG")
    
    return export_dir, test_data


class TestDirectoryGenerator:
    """Test the DirectoryGenerator class functionality."""
    pass


class TestValidation:
    """Test export validation functionality."""
    
    def test_validate_export_success(self, test_export_dir, tmp_path):
        """Test successful export validation."""
        export_dir, _ = test_export_dir
        generator = DirectoryGenerator(export_dir, tmp_path / "output")
        assert generator.validate_export() is True
    
    def test_validate_export_missing_directory(self, tmp_path):
        """Test validation with missing directory."""
        missing_dir = tmp_path / "nonexistent"
        generator = DirectoryGenerator(missing_dir)
        assert generator.validate_export() is False
    
    def test_validate_export_not_directory(self, tmp_path):
        """Test validation when path is a file, not directory."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("test")
        generator = DirectoryGenerator(file_path)
        assert generator.validate_export() is False
    
    def test_validate_export_missing_json(self, tmp_path):
        """Test validation with missing JSON file."""
        empty_dir = tmp_path / "empty_export"
        empty_dir.mkdir()
        generator = DirectoryGenerator(empty_dir)
        assert generator.validate_export() is False


class TestDataLoading:
    """Test data loading and parsing functionality."""
    
    def test_load_export_data_contacts(self, test_export_dir, tmp_path):
        """Test loading contacts export data."""
        export_dir, expected_data = test_export_dir
        generator = DirectoryGenerator(export_dir, tmp_path / "output")
        
        assert generator.validate_export() is True
        assert generator.load_export_data() is True
        assert generator.export_data == expected_data
    
    def test_load_export_data_tags(self, tags_export_dir, tmp_path):
        """Test loading tags export data."""
        export_dir, expected_data = tags_export_dir
        generator = DirectoryGenerator(export_dir, tmp_path / "output")
        
        assert generator.validate_export() is True
        assert generator.load_export_data() is True
        assert generator.export_data == expected_data
    
    def test_load_export_data_notes(self, notes_export_dir, tmp_path):
        """Test loading notes export data."""
        export_dir, expected_data = notes_export_dir
        generator = DirectoryGenerator(export_dir, tmp_path / "output")
        
        assert generator.validate_export() is True
        assert generator.load_export_data() is True
        assert generator.export_data == expected_data


class TestContactExtraction:
    """Test contact extraction and relationship detection."""
    
    def test_extract_contacts_from_contacts_search(self, test_export_dir, tmp_path):
        """Test extracting contacts from contacts search."""
        export_dir, _ = test_export_dir
        generator = DirectoryGenerator(export_dir, tmp_path / "output")
        generator.validate_export()
        generator.load_export_data()
        
        contacts = generator.extract_contacts()
        
        assert len(contacts) == 6
        # Verify first contact (John Doe)
        assert contacts[0]["name"] == "John Doe"
        assert contacts[0]["email"] == "john.doe@example.com"
        assert contacts[0]["has_profile_image"] is True
        assert "friend" in contacts[0]["relationship_info"]["tags"]
        assert "family" in contacts[0]["relationship_info"]["tags"]
        
        # Verify Alice Johnson is present
        alice = next((c for c in contacts if c["name"] == "Alice Johnson"), None)
        assert alice is not None
        assert alice["email"] == "alice.johnson@gmail.com"
        assert alice["has_profile_image"] is True
        
        # Verify Charlie Brown (no image)
        charlie = next((c for c in contacts if c["name"] == "Charlie Brown"), None)
        assert charlie is not None
        assert charlie["has_profile_image"] is False
    
    def test_extract_contacts_from_tags_search(self, tags_export_dir, tmp_path):
        """Test extracting contacts from tags search with relationships."""
        export_dir, _ = tags_export_dir
        generator = DirectoryGenerator(export_dir, tmp_path / "output")
        generator.validate_export()
        generator.load_export_data()
        
        contacts = generator.extract_contacts()
        
        assert len(contacts) == 3
        
        # Check unique contacts
        names = [c["name"] for c in contacts]
        assert "Alice Johnson" in names
        assert "Bob Wilson" in names
        assert "Carol Davis" in names
        
        # Check tags are preserved
        alice = next(c for c in contacts if c["name"] == "Alice Johnson")
        assert "friend" in alice["relationship_info"]["tags"]
        assert "coworker" in alice["relationship_info"]["tags"]
    
    def test_extract_contacts_from_notes_search(self, notes_export_dir, tmp_path):
        """Test extracting contacts from notes search."""
        export_dir, _ = notes_export_dir
        generator = DirectoryGenerator(export_dir, tmp_path / "output")
        generator.validate_export()
        generator.load_export_data()
        
        contacts = generator.extract_contacts()
        
        assert len(contacts) == 2
        assert contacts[0]["name"] == "Alice Johnson"
        assert contacts[1]["name"] == "Bob Wilson"
        
        # Check notes are preserved
        alice = contacts[0]
        assert len(alice["relationship_info"]["notes"]) == 1
        assert alice["relationship_info"]["notes"][0]["title"] == "Team Meeting"


class TestFileGeneration:
    """Test file generation functionality."""
    
    def test_create_output_directory(self, test_export_dir, tmp_path):
        """Test output directory creation."""
        export_dir, _ = test_export_dir
        output_dir = tmp_path / "test_output"
        generator = DirectoryGenerator(export_dir, output_dir)
        
        assert generator.create_output_directory() is True
        assert output_dir.exists()
        assert output_dir.is_dir()
    
    def test_copy_profile_images(self, test_export_dir, tmp_path):
        """Test profile image copying."""
        export_dir, _ = test_export_dir
        output_dir = tmp_path / "test_output"
        generator = DirectoryGenerator(export_dir, output_dir)
        generator.validate_export()
        generator.load_export_data()
        generator.create_output_directory()
        generator.extract_contacts()
        
        copied_count = generator.copy_profile_images()
        
        assert copied_count == 5  # 5 contacts have images (all except Charlie Brown)
        assert (output_dir / "images" / "1.jpg").exists()
        assert (output_dir / "images" / "2.jpg").exists()
        assert (output_dir / "images" / "3.jpg").exists()
        assert (output_dir / "images" / "4.jpg").exists()
        assert (output_dir / "images" / "6.jpg").exists()
        
        # Verify image is valid
        img = Image.open(output_dir / "images" / "1.jpg")
        assert img.size == (256, 256)
    
    def test_copy_profile_images_no_images(self, tags_export_dir, tmp_path):
        """Test profile image copying when no images exist."""
        export_dir, _ = tags_export_dir
        output_dir = tmp_path / "test_output"
        generator = DirectoryGenerator(export_dir, output_dir)
        generator.create_output_directory()
        
        copied_count = generator.copy_profile_images()
        
        assert copied_count == 0
    
    def test_generate_data_js(self, test_export_dir, tmp_path):
        """Test data.js generation."""
        export_dir, _ = test_export_dir
        output_dir = tmp_path / "test_output"
        generator = DirectoryGenerator(export_dir, output_dir)
        generator.validate_export()
        generator.load_export_data()
        generator.create_output_directory()
        generator.extract_contacts()
        
        assert generator.generate_data_js() is True
        
        data_js_file = output_dir / "data.js"
        assert data_js_file.exists()
        
        # Read and verify data.js content
        content = data_js_file.read_text()
        assert "const contactData = {" in content
        assert '"export_info":' in content
        assert '"nodes":' in content
        assert '"links":' in content
        assert '"John Doe"' in content
        assert '"Jane Smith"' in content
        assert '"Alice Johnson"' in content
        assert '"Bob Wilson"' in content
        assert '"Charlie Brown"' in content
        assert '"Diana Prince"' in content
    
    def test_generate_html(self, test_export_dir, tmp_path):
        """Test HTML generation with D3.js visualization."""
        export_dir, _ = test_export_dir
        output_dir = tmp_path / "test_output"
        generator = DirectoryGenerator(export_dir, output_dir)
        generator.validate_export()
        generator.load_export_data()
        generator.create_output_directory()
        
        assert generator.generate_html() is True
        
        html_file = output_dir / "index.html"
        assert html_file.exists()
        
        content = html_file.read_text()
        
        # Check essential HTML structure
        assert "<!DOCTYPE html>" in content
        assert "<title>Contact Directory - alice</title>" in content
        assert "d3js.org/d3.v7.min.js" in content
        
        # Check D3.js visualization code
        assert "d3.forceSimulation" in content
        assert "d3.zoom()" in content
        assert "touch-action: none" in content
        
        # Check mobile optimization
        assert "@media (max-width: 768px)" in content
        assert "min-height: 44px" in content
        
        # Check search metadata display
        assert "Contacts search for" in content
        assert "contactData.nodes.length" in content


class TestFullWorkflow:
    """Test complete workflow from start to finish."""
    
    def test_full_generation_contacts_with_images(self, test_export_dir, tmp_path):
        """Test complete generation workflow with contacts and images."""
        export_dir, _ = test_export_dir
        output_dir = tmp_path / "full_test_contacts"
        generator = DirectoryGenerator(export_dir, output_dir)
        
        # Test full generation
        result = generator.generate()
        assert result is True
        
        # Verify all files were created
        assert (output_dir / "index.html").exists()
        assert (output_dir / "data.js").exists()
        assert (output_dir / "images" / "1.jpg").exists()
        
        # Verify HTML content structure
        html_content = (output_dir / "index.html").read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "Contact Directory - alice" in html_content
        assert "d3js.org/d3.v7.min.js" in html_content
        assert "d3.forceSimulation" in html_content
        
                # Verify data.js content quality
        data_content = (output_dir / "data.js").read_text()
        assert '"id": 1' in data_content
        assert '"name": "John Doe"' in data_content
        assert '"has_image": true' in data_content
        assert '"email": "john.doe@example.com"' in data_content
        # Verify all 6 contacts are present
        assert '"name": "Alice Johnson"' in data_content
        assert '"name": "Jane Smith"' in data_content
        assert '"name": "Bob Wilson"' in data_content
        assert '"name": "Charlie Brown"' in data_content
        assert '"name": "Diana Prince"' in data_content
        assert '"friend"' in data_content
        assert '"family"' in data_content
        assert '"links": [' in data_content
        assert '"relationship":' in data_content
        
        # Print location for manual verification
        print(f"\n🌐 Manual verification URL: file://{output_dir.absolute()}/index.html")
    
    def test_full_generation_tags_with_relationships(self, tags_export_dir, tmp_path):
        """Test complete generation workflow with tag relationships."""
        export_dir, _ = tags_export_dir
        output_dir = tmp_path / "full_test_tags"
        generator = DirectoryGenerator(export_dir, output_dir)
        
        result = generator.generate()
        assert result is True
        
        # Verify relationship detection
        data_content = (output_dir / "data.js").read_text()
        assert '"links":' in data_content
        assert '"source":' in data_content
        assert '"target":' in data_content
        assert '"strength":' in data_content
        
        # Should have relationships between contacts with shared tags
        assert '"Alice Johnson"' in data_content
        assert '"Bob Wilson"' in data_content
        assert '"Carol Davis"' in data_content
        
        print(f"\n🌐 Manual verification URL: file://{output_dir.absolute()}/index.html")
    
    def test_full_generation_notes_search(self, notes_export_dir, tmp_path):
        """Test complete generation workflow with notes search."""
        export_dir, _ = notes_export_dir
        output_dir = tmp_path / "full_test_notes"
        generator = DirectoryGenerator(export_dir, output_dir)
        
        result = generator.generate()
        assert result is True
        
        # Verify files created
        assert (output_dir / "index.html").exists()
        assert (output_dir / "data.js").exists()
        assert (output_dir / "images" / "1.jpg").exists()
        
        # Verify notes search metadata
        html_content = (output_dir / "index.html").read_text()
        assert "Notes search for" in html_content
        assert "meeting" in html_content
        
        print(f"\n🌐 Manual verification URL: file://{output_dir.absolute()}/index.html")


class TestCLI:
    """Test the CLI interface."""
    
    def test_cli_generate_command(self, test_export_dir, tmp_path):
        """Test the CLI generate command."""
        export_dir, _ = test_export_dir
        output_dir = tmp_path / "cli_test"
        
        runner = CliRunner()
        result = runner.invoke(app, [
            "generate", 
            str(export_dir),
            "--output", str(output_dir),
            "--force"
        ])
        
        assert result.exit_code == 0
        assert "Generation Complete" in result.stdout
        assert (output_dir / "index.html").exists()
        assert (output_dir / "data.js").exists()
        
        print(f"\n🌐 CLI Test URL: file://{output_dir.absolute()}/index.html")
    
    def test_cli_info_command(self):
        """Test the CLI info command."""
        runner = CliRunner()
        result = runner.invoke(app, ["info"])
        
        assert result.exit_code == 0
        assert "make_directory.py" in result.stdout
        assert "Phase" in result.stdout
    
    def test_cli_help(self):
        """Test CLI help functionality."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Generate interactive contact directories" in result.stdout


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_json_file(self, tmp_path):
        """Test handling of invalid JSON files."""
        export_dir = tmp_path / "invalid_export"
        export_dir.mkdir()
        
        # Create invalid JSON file
        json_file = export_dir / "contacts_search_results.json"
        json_file.write_text("{ invalid json content")
        
        generator = DirectoryGenerator(export_dir)
        assert generator.validate_export() is True  # JSON file exists
        assert generator.load_export_data() is False  # But loading fails
    
    def test_missing_required_fields(self, tmp_path):
        """Test handling of JSON with missing required fields."""
        export_dir = tmp_path / "incomplete_export"
        export_dir.mkdir()
        
        # Create JSON with missing fields
        incomplete_data = {
            "export_info": {
                "timestamp": "20250826_123456"
                # Missing search_type, query, total_results
            }
            # Missing results
        }
        
        json_file = export_dir / "contacts_search_results.json"
        with open(json_file, 'w') as f:
            json.dump(incomplete_data, f)
        
        generator = DirectoryGenerator(export_dir)
        assert generator.validate_export() is True
        
        # Should handle gracefully even with missing fields
        generator.load_export_data()
        # Implementation should handle missing fields gracefully
    
    def test_empty_results(self, tmp_path):
        """Test handling of exports with no results."""
        export_dir = tmp_path / "empty_export"
        export_dir.mkdir()
        
        empty_data = {
            "search_request": {
                "type": "contacts",
                "term": "nonexistent",
                "executed_at": "2025-08-26T12:34:56"
            },
            "export_info": {
                "search_type": "contacts",
                "query": "nonexistent",
                "timestamp": "20250826_123456",
                "total_results": 0
            },
            "results": []
        }
        
        json_file = export_dir / "contacts_search_results.json"
        with open(json_file, 'w') as f:
            json.dump(empty_data, f)
        
        generator = DirectoryGenerator(export_dir)
        result = generator.generate()
        
        # Should still generate files even with no results
        assert result is True
        assert (generator.output_path / "index.html").exists()
        assert (generator.output_path / "data.js").exists()


if __name__ == "__main__":
    # Run tests with verbose output showing manual verification URLs
    pytest.main([__file__, "-v", "-s"])
