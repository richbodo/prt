#!/usr/bin/env python3
"""
make_directory.py - PRT Contact Directory Generator

Creates interactive single-page websites from PRT JSON exports showing 
contact relationships as navigable 2D graphs.

Usage:
    make_directory.py exports/contacts_search_20250826_191055/
    make_directory.py exports/tags_search_20250826_191055/ --output ./my_directory
"""

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

app = typer.Typer(help="Generate interactive contact directories from PRT exports")
console = Console()


class DirectoryGenerator:
    """Handles the generation of contact directory websites."""
    
    def __init__(self, export_path: Path, output_path: Optional[Path] = None):
        self.export_path = Path(export_path)
        self.output_path = output_path or Path("directories") / self.export_path.name
        self.export_data = None
        self.contact_data = []
        
    def validate_export(self) -> bool:
        """Validate that the export directory contains required files."""
        if not self.export_path.exists():
            console.print(f"❌ Export directory not found: {self.export_path}", style="red")
            return False
            
        if not self.export_path.is_dir():
            console.print(f"❌ Path is not a directory: {self.export_path}", style="red")
            return False
            
        # Look for JSON file
        json_files = list(self.export_path.glob("*_search_results.json"))
        if not json_files:
            console.print("❌ No search results JSON file found in export directory", style="red")
            return False
            
        self.json_file = json_files[0]
        
        # Check for profile images directory
        images_dir = self.export_path / "profile_images"
        if not images_dir.exists():
            console.print("⚠️  No profile_images directory found - contacts will show without images", style="yellow")
        
        return True
    
    def load_export_data(self) -> bool:
        """Load and parse the JSON export data."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                self.export_data = json.load(f)
            
            # Validate JSON structure
            if "export_info" not in self.export_data or "results" not in self.export_data:
                console.print("❌ Invalid JSON structure - missing export_info or results", style="red")
                return False
                
            console.print(f"✅ Loaded export data: {self.export_data['export_info']['search_type']} search", style="green")
            console.print(f"   Query: '{self.export_data['export_info']['query']}'", style="dim")
            console.print(f"   Results: {self.export_data['export_info']['total_results']}", style="dim")
            
            return True
            
        except json.JSONDecodeError as e:
            console.print(f"❌ Invalid JSON file: {e}", style="red")
            return False
        except Exception as e:
            console.print(f"❌ Error loading export data: {e}", style="red")
            return False
    
    def extract_contacts(self) -> List[Dict[str, Any]]:
        """Extract contact data from different search result types."""
        contacts = []
        search_type = self.export_data["export_info"]["search_type"]
        
        if search_type == "contacts":
            # Direct contact search results
            contacts = self.export_data["results"]
            
        elif search_type == "tags":
            # Extract contacts from tag results
            for tag_result in self.export_data["results"]:
                if "associated_contacts" in tag_result:
                    contacts.extend(tag_result["associated_contacts"])
                    
        elif search_type == "notes":
            # Extract contacts from note results  
            for note_result in self.export_data["results"]:
                if "associated_contacts" in note_result:
                    contacts.extend(note_result["associated_contacts"])
        
        # Remove duplicates based on contact ID
        unique_contacts = {}
        for contact in contacts:
            if contact["id"] not in unique_contacts:
                unique_contacts[contact["id"]] = contact
        
        self.contact_data = list(unique_contacts.values())
        console.print(f"📊 Extracted {len(self.contact_data)} unique contacts", style="blue")
        
        return self.contact_data
    
    def create_output_directory(self) -> bool:
        """Create the output directory structure."""
        try:
            self.output_path.mkdir(parents=True, exist_ok=True)
            (self.output_path / "images").mkdir(exist_ok=True)
            
            console.print(f"📁 Created output directory: {self.output_path}", style="green")
            return True
            
        except Exception as e:
            console.print(f"❌ Error creating output directory: {e}", style="red")
            return False
    
    def copy_profile_images(self) -> int:
        """Copy profile images to the output directory."""
        images_copied = 0
        images_dir = self.export_path / "profile_images"
        output_images_dir = self.output_path / "images"
        
        if not images_dir.exists():
            console.print("⚠️  No profile images to copy", style="yellow")
            return 0
        
        for contact in self.contact_data:
            if contact.get("has_profile_image") and contact.get("exported_image_path"):
                source_image = self.export_path / contact["exported_image_path"]
                if source_image.exists():
                    # Copy with the same filename (contact_id.jpg)
                    dest_image = output_images_dir / source_image.name
                    shutil.copy2(source_image, dest_image)
                    images_copied += 1
        
        if images_copied > 0:
            console.print(f"🖼️  Copied {images_copied} profile images", style="green")
        
        return images_copied
    
    def generate_data_js(self) -> bool:
        """Generate JavaScript data file for the visualization."""
        try:
            # Prepare data for D3.js
            nodes = []
            links = []
            
            # Create nodes for each contact
            for contact in self.contact_data:
                node = {
                    "id": contact["id"],
                    "name": contact["name"],
                    "email": contact.get("email", ""),
                    "phone": contact.get("phone", ""),
                    "has_image": contact.get("has_profile_image", False),
                    "image_path": f"images/{contact['id']}.jpg" if contact.get("has_profile_image") else None,
                    "tags": contact.get("relationship_info", {}).get("tags", []),
                    "notes": contact.get("relationship_info", {}).get("notes", [])
                }
                nodes.append(node)
            
            # Create links based on shared tags (simple relationship detection)
            for i, contact1 in enumerate(self.contact_data):
                tags1 = set(contact1.get("relationship_info", {}).get("tags", []))
                for j, contact2 in enumerate(self.contact_data[i+1:], i+1):
                    tags2 = set(contact2.get("relationship_info", {}).get("tags", []))
                    shared_tags = tags1.intersection(tags2)
                    
                    if shared_tags:
                        links.append({
                            "source": contact1["id"],
                            "target": contact2["id"],
                            "relationship": list(shared_tags),
                            "strength": len(shared_tags)
                        })
            
            # Generate JavaScript file
            js_data = {
                "export_info": self.export_data["export_info"],
                "nodes": nodes,
                "links": links,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_contacts": len(nodes),
                    "total_relationships": len(links)
                }
            }
            
            js_content = f"// Contact directory data - generated by make_directory.py\nconst contactData = {json.dumps(js_data, indent=2)};\n"
            
            with open(self.output_path / "data.js", 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            console.print(f"📄 Generated data.js with {len(nodes)} contacts and {len(links)} relationships", style="green")
            return True
            
        except Exception as e:
            console.print(f"❌ Error generating data.js: {e}", style="red")
            return False
    
    def generate_html(self) -> bool:
        """Generate the main HTML file (placeholder for Phase 1)."""
        try:
            # Basic HTML template (will be enhanced in Phase 2)
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Directory</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .contact-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .contact-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        .contact-image {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            margin: 0 auto 10px;
            display: block;
            background: #ddd;
        }
        .contact-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .contact-email {
            color: #666;
            font-size: 0.9em;
        }
        .tags {
            margin-top: 10px;
        }
        .tag {
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Contact Directory</h1>
        <p>Interactive visualization coming in Phase 2!</p>
    </div>
    
    <div class="contact-grid" id="contacts">
        <!-- Contacts will be populated by JavaScript -->
    </div>
    
    <script src="data.js"></script>
    <script>
        // Simple contact display for Phase 1
        function displayContacts() {
            const container = document.getElementById('contacts');
            
            contactData.nodes.forEach(contact => {
                const card = document.createElement('div');
                card.className = 'contact-card';
                
                const img = document.createElement('img');
                img.className = 'contact-image';
                img.src = contact.has_image ? contact.image_path : 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA4MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iNDAiIGN5PSI0MCIgcj0iNDAiIGZpbGw9IiNEREQiLz4KPHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4PSIyMCIgeT0iMjAiPgo8cGF0aCBkPSJNMTIgMTJDMTQuMjEgMTIgMTYgMTAuMjEgMTYgOEMxNiA1Ljc5IDE0LjIxIDQgMTIgNEM5Ljc5IDQgOCA1Ljc5IDggOEM4IDEwLjIxIDkuNzkgMTIgMTIgMTJaTTEyIDE0QzguNjkgMTQgMiAxNS4zNCAyIDE5VjIxSDIyVjE5QzIyIDE1LjM0IDE1LjMxIDE0IDEyIDE0WiIgZmlsbD0iIzk5OSIvPgo8L3N2Zz4KPC9zdmc+';
                img.alt = contact.name;
                img.onerror = function() {
                    this.style.display = 'none';
                };
                
                const name = document.createElement('div');
                name.className = 'contact-name';
                name.textContent = contact.name;
                
                const email = document.createElement('div');
                email.className = 'contact-email';
                email.textContent = contact.email || 'No email';
                
                const tags = document.createElement('div');
                tags.className = 'tags';
                contact.tags.forEach(tag => {
                    const tagEl = document.createElement('span');
                    tagEl.className = 'tag';
                    tagEl.textContent = tag;
                    tags.appendChild(tagEl);
                });
                
                card.appendChild(img);
                card.appendChild(name);
                card.appendChild(email);
                card.appendChild(tags);
                
                container.appendChild(card);
            });
        }
        
        // Display contacts when page loads
        displayContacts();
        
        // Log data for debugging
        console.log('Contact Data:', contactData);
    </script>
</body>
</html>"""
            
            with open(self.output_path / "index.html", 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            console.print("📄 Generated index.html with basic contact display", style="green")
            return True
            
        except Exception as e:
            console.print(f"❌ Error generating HTML: {e}", style="red")
            return False
    
    def generate(self) -> bool:
        """Main generation process."""
        console.print("🚀 Starting contact directory generation...", style="bold blue")
        
        # Step 1: Validate export
        if not self.validate_export():
            return False
        
        # Step 2: Load data
        if not self.load_export_data():
            return False
        
        # Step 3: Extract contacts
        self.extract_contacts()
        
        if not self.contact_data:
            console.print("❌ No contacts found in export data", style="red")
            return False
        
        # Step 4: Create output directory
        if not self.create_output_directory():
            return False
        
        # Step 5: Copy images
        self.copy_profile_images()
        
        # Step 6: Generate data file
        if not self.generate_data_js():
            return False
        
        # Step 7: Generate HTML
        if not self.generate_html():
            return False
        
        # Success!
        success_text = Text()
        success_text.append("✅ Contact directory generated successfully!\n\n", style="bold green")
        success_text.append(f"📁 Output: ", style="bold")
        success_text.append(f"{self.output_path.absolute()}\n", style="blue")
        success_text.append(f"🌐 Open: ", style="bold")
        success_text.append(f"file://{self.output_path.absolute()}/index.html\n", style="blue")
        
        console.print(Panel(success_text, title="Generation Complete", border_style="green"))
        
        return True


@app.command()
def generate(
    export_dir: str = typer.Argument(..., help="Path to PRT export directory"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory (default: directories/{export_name})"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing output directory")
):
    """Generate an interactive contact directory from a PRT export."""
    
    export_path = Path(export_dir)
    output_path = Path(output) if output else None
    
    # Check if output exists and handle force flag
    final_output_path = output_path or Path("directories") / export_path.name
    if final_output_path.exists() and not force:
        if not typer.confirm(f"Output directory '{final_output_path}' exists. Overwrite?"):
            console.print("❌ Operation cancelled", style="red")
            raise typer.Exit(1)
    
    # Generate the directory
    generator = DirectoryGenerator(export_path, output_path)
    success = generator.generate()
    
    if not success:
        console.print("❌ Directory generation failed", style="red")
        raise typer.Exit(1)


@app.command()
def info():
    """Show information about make_directory.py."""
    info_text = Text()
    info_text.append("make_directory.py - PRT Contact Directory Generator\n\n", style="bold blue")
    info_text.append("Creates interactive single-page websites from PRT JSON exports.\n", style="white")
    info_text.append("Shows contact relationships as navigable 2D graphs.\n\n", style="white")
    info_text.append("Phase 1: Basic HTML generation with contact cards\n", style="dim")
    info_text.append("Phase 2: D3.js interactive graph visualization (coming soon)\n", style="dim")
    info_text.append("Phase 3: Mobile support and advanced features\n", style="dim")
    
    console.print(Panel(info_text, title="About", border_style="blue"))


if __name__ == "__main__":
    app()
