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
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

app = typer.Typer(help="Generate interactive contact directories from PRT exports")
console = Console()


class DirectoryGenerator:
    """Handles the generation of contact directory websites."""

    def __init__(
        self,
        export_path: Path,
        output_path: Optional[Path] = None,
        layout: str = "graph",
    ):
        self.export_path = Path(export_path)
        self.output_path = output_path or Path("directories") / self.export_path.name
        self.export_data = None
        self.contact_data = []
        self.layout = layout

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
            console.print(
                "⚠️  No profile_images directory found - contacts will show without images",
                style="yellow",
            )

        return True

    def load_export_data(self) -> bool:
        """Load and parse the JSON export data."""
        try:
            with open(self.json_file, encoding="utf-8") as f:
                self.export_data = json.load(f)

            # Validate JSON structure
            if "export_info" not in self.export_data or "results" not in self.export_data:
                console.print(
                    "❌ Invalid JSON structure - missing export_info or results", style="red"
                )
                return False

            console.print(
                f"✅ Loaded export data: {self.export_data['export_info']['search_type']} search",
                style="green",
            )
            console.print(f"   Query: '{self.export_data['export_info']['query']}'", style="dim")
            console.print(
                f"   Results: {self.export_data['export_info']['total_results']}", style="dim"
            )

            return True

        except json.JSONDecodeError as e:
            console.print(f"❌ Invalid JSON file: {e}", style="red")
            return False
        except Exception as e:
            console.print(f"❌ Error loading export data: {e}", style="red")
            return False

    def extract_contacts(self) -> list[dict[str, Any]]:
        """Extract contact data from different search result types."""
        contacts = []
        search_type = self.export_data["export_info"]["search_type"]

        if search_type == "contacts":
            # Direct contact search results - results are contact objects
            for result in self.export_data["results"]:
                if "id" in result:  # Direct contact object
                    contacts.append(result)
                elif "contact" in result and "id" in result["contact"]:  # Nested contact object
                    contacts.append(result["contact"])

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
            if "id" in contact and contact["id"] not in unique_contacts:
                unique_contacts[contact["id"]] = contact

        self.contact_data = list(unique_contacts.values())
        console.print(f"📊 Extracted {len(self.contact_data)} unique contacts", style="blue")

        return self.contact_data

    def build_nodes(self) -> list[dict[str, Any]]:
        """Transform contact data into node dictionaries."""
        nodes: list[dict[str, Any]] = []
        for contact in self.contact_data:
            node = {
                "id": contact["id"],
                "name": contact["name"],
                "email": contact.get("email", ""),
                "phone": contact.get("phone", ""),
                "has_image": contact.get("has_profile_image", False),
                "image_path": (
                    f"images/{contact['id']}.jpg"
                    if contact.get("has_profile_image")
                    else "images/default.svg"
                ),
                "tags": contact.get("relationship_info", {}).get("tags", []),
                "notes": contact.get("relationship_info", {}).get("notes", []),
            }
            nodes.append(node)

        return nodes

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
                    try:
                        shutil.copy2(source_image, dest_image)
                        images_copied += 1
                    except OSError as e:
                        console.print(f"❌ Failed to copy {source_image}: {e}", style="red")

        if images_copied > 0:
            console.print(f"🖼️  Copied {images_copied} profile images", style="green")

        return images_copied

    def generate_data_js(self) -> bool:
        """Generate JavaScript data file for the visualization."""
        try:
            # Prepare data for D3.js
            nodes = self.build_nodes()
            links = []

            # Create links based on shared tags (simple relationship detection)
            for i, contact1 in enumerate(self.contact_data):
                tags1 = set(contact1.get("relationship_info", {}).get("tags", []))
                for _j, contact2 in enumerate(self.contact_data[i + 1 :], i + 1):
                    tags2 = set(contact2.get("relationship_info", {}).get("tags", []))
                    shared_tags = tags1.intersection(tags2)

                    if shared_tags:
                        links.append(
                            {
                                "source": contact1["id"],
                                "target": contact2["id"],
                                "relationship": list(shared_tags),
                                "strength": len(shared_tags),
                            }
                        )

            # Generate JavaScript file
            js_data = {
                "export_info": self.export_data["export_info"],
                "nodes": nodes,
                "links": links,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_contacts": len(nodes),
                    "total_relationships": len(links),
                },
            }

            js_content = f"// Contact directory data - generated by make_directory.py\nconst contactData = {json.dumps(js_data, indent=2)};\n"

            with open(self.output_path / "data.js", "w", encoding="utf-8") as f:
                f.write(js_content)

            console.print(
                f"📄 Generated data.js with {len(nodes)} contacts and {len(links)} relationships",
                style="green",
            )
            return True

        except Exception as e:
            console.print(f"❌ Error generating data.js: {e}", style="red")
            return False

    def generate_graph_html(self) -> bool:
        """Generate the D3.js force-directed graph HTML."""
        try:
            # Get export metadata for display
            export_info = self.export_data["export_info"]
            search_type = export_info["search_type"]
            query = export_info["query"]

            # Advanced HTML template with D3.js force-directed graph
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Directory - {query}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            overflow: hidden;
        }}

        .header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            z-index: 1000;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .header h1 {{
            font-size: 1.5em;
            font-weight: 600;
            color: #333;
        }}

        .header .search-info {{
            font-size: 0.9em;
            color: #666;
        }}

        .controls {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}

        .btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85em;
            transition: background 0.2s;
        }}

        .btn:hover {{
            background: #5a6fd8;
        }}

        .btn.secondary {{
            background: #6c757d;
        }}

        .btn.secondary:hover {{
            background: #545b62;
        }}

        #graph {{
            position: fixed;
            top: 70px;
            left: 0;
            right: 0;
            bottom: 0;
            background: #f8f9fa;
        }}

        .node {{
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }}

        .node:hover {{
            stroke: #667eea;
            stroke-width: 3px;
        }}

        .node-image {{
            clip-path: circle(50%);
        }}

        .node-text {{
            font-size: 12px;
            font-weight: 600;
            text-anchor: middle;
            pointer-events: none;
            fill: #333;
            text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8);
        }}

        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
            stroke-width: 2px;
        }}

        .link.strong {{
            stroke: #667eea;
            stroke-width: 3px;
            stroke-opacity: 0.8;
        }}

        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px;
            border-radius: 6px;
            font-size: 0.9em;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            max-width: 250px;
            z-index: 1001;
        }}

        .tooltip .name {{
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .tooltip .detail {{
            margin-bottom: 3px;
        }}

        .tags {{
            margin-top: 8px;
        }}

        .tag {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.75em;
            margin: 1px;
        }}

        .legend {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 15px;
            border-radius: 8px;
            font-size: 0.85em;
            border: 1px solid rgba(0, 0, 0, 0.1);
        }}

        .legend h3 {{
            margin-bottom: 8px;
            font-size: 0.9em;
        }}

        .legend-item {{
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}

        @media (max-width: 768px) {{
            .header {{
                flex-direction: column;
                gap: 10px;
                padding: 10px;
            }}

            .header h1 {{
                font-size: 1.2em;
            }}

            .controls {{
                flex-wrap: wrap;
            }}

            .btn {{
                font-size: 0.8em;
                padding: 8px 16px;
                min-height: 44px; /* Touch-friendly size */
                min-width: 80px;
            }}

            .legend {{
                bottom: 10px;
                right: 10px;
                left: 10px;
                max-width: none;
                font-size: 0.8em;
            }}

            #graph {{
                top: 100px; /* More space for mobile header */
            }}

            .node {{
                stroke-width: 3px; /* Thicker stroke for touch */
            }}

            .node-text {{
                font-size: 13px; /* Larger text for mobile */
            }}

            .tooltip {{
                font-size: 0.85em;
                max-width: 200px;
                padding: 12px;
            }}
        }}

        /* Touch-specific improvements */
        .node, .node-image {{
            touch-action: none; /* Prevent scrolling when dragging nodes */
        }}

        #graph {{
            touch-action: none; /* Enable touch gestures for zoom/pan */
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>Contact Directory</h1>
            <div class="search-info">
                {search_type.title()} search for "{query}" • {{contactData.nodes.length}} contacts
            </div>
        </div>
        <div class="controls">
            <button class="btn" onclick="resetView()">Reset View</button>
            <button class="btn secondary" onclick="toggleMode()">Grid View</button>
        </div>
    </div>

    <div id="graph"></div>
    <div class="tooltip" id="tooltip"></div>

    <div class="legend">
        <h3>Legend</h3>
        <div class="legend-item">
            <div class="legend-color" style="background: #28a745;"></div>
            <span>Contact with image</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #6c757d;"></div>
            <span>Contact without image</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #667eea; width: 20px; height: 3px; border-radius: 2px;"></div>
            <span>Relationship connection</span>
        </div>
    </div>

    <script src="data.js"></script>
    <script>
        // Global variables
        let svg, simulation, node, link, tooltip;
        let width, height;
        let isGridMode = false;

        // Initialize the visualization
        function initGraph() {{
            // Set up dimensions
            const container = d3.select("#graph");
            const containerNode = container.node();
            const rect = containerNode.getBoundingClientRect();
            width = rect.width;
            height = rect.height;

            // Create SVG with mobile-optimized zoom
            svg = container.append("svg")
                .attr("width", width)
                .attr("height", height)
                .call(d3.zoom()
                    .scaleExtent([0.1, 4])
                    .filter((event) => {{
                        // Allow zoom/pan but prevent conflicts with node dragging
                        return !event.ctrlKey && !event.button;
                    }})
                    .on("zoom", (event) => {{
                        svg.select("g").attr("transform", event.transform);
                    }}));

            const g = svg.append("g");

            // Create tooltip
            tooltip = d3.select("#tooltip");

            // Prepare data with central "YOU" node
            const originalNodes = contactData.nodes.map(d => ({{...d}}));
            const originalLinks = contactData.links.map(d => ({{...d}}));

            // Add central "YOU" node
            const centerNode = {{
                id: "you",
                name: "YOU",
                isCenter: true,
                x: width / 2,
                y: height / 2,
                fx: width / 2, // Fix position at center
                fy: height / 2
            }};

            // Create user-centric nodes array
            const nodes = [centerNode, ...originalNodes];

            // Create links from center to all contacts
            const userLinks = originalNodes.map(node => ({{
                source: "you",
                target: node.id,
                strength: 1,
                isUserLink: true
            }}));

            // Combine with existing relationship links
            const links = [...userLinks, ...originalLinks];

            // Set up simulation with user-centric layout
            simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id(d => d.id).distance(d => d.isUserLink ? 120 : 80))
                .force("charge", d3.forceManyBody().strength(d => d.isCenter ? -1000 : -200))
                .force("collision", d3.forceCollide().radius(d => d.isCenter ? 50 : 35))
                .alphaDecay(0.05) // Slower decay for smoother animation
                .velocityDecay(0.8); // Better mobile performance

            // Create links
            link = g.selectAll(".link")
                .data(links)
                .enter().append("line")
                .attr("class", d => {{
                    if (d.isUserLink) return "link user-link";
                    return `link ${{d.strength > 1 ? 'strong' : ''}}`;
                }})
                .attr("stroke", d => d.isUserLink ? "#007bff" : null)
                .attr("stroke-width", d => d.isUserLink ? 2 : Math.max(1, d.strength * 2))
                .attr("stroke-dasharray", d => d.isUserLink ? "5,5" : null);

            // Create nodes
            const nodeGroup = g.selectAll(".node-group")
                .data(nodes)
                .enter().append("g")
                .attr("class", "node-group")
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));

            // Add circles for nodes - different styling for center node
            node = nodeGroup.append("circle")
                .attr("class", d => d.isCenter ? "node center-node" : "node")
                .attr("r", d => d.isCenter ? 40 : 25)
                .attr("fill", d => {{
                    if (d.isCenter) return "#007bff"; // Blue for center
                    return d.has_image ? "#28a745" : "#6c757d";
                }})
                .attr("stroke", d => d.isCenter ? "#ffffff" : "none")
                .attr("stroke-width", d => d.isCenter ? 3 : 0)
                .on("mouseover", showTooltip)
                .on("mousemove", moveTooltip)
                .on("mouseout", hideTooltip)
                .on("click", handleNodeClick);

            // Add images for contact nodes with profile pictures
            nodeGroup.filter(d => d.has_image && !d.isCenter)
                .append("image")
                .attr("class", "node-image")
                .attr("href", d => d.image_path)
                .attr("x", -22)
                .attr("y", -22)
                .attr("width", 44)
                .attr("height", 44)
                .style("clip-path", "circle(50%)")
                .on("mouseover", showTooltip)
                .on("mousemove", moveTooltip)
                .on("mouseout", hideTooltip)
                .on("click", handleNodeClick);

            // Add text labels
            nodeGroup.append("text")
                .attr("class", d => d.isCenter ? "node-text center-text" : "node-text")
                .attr("y", d => d.isCenter ? 5 : 35)  // Center text in middle, others below
                .text(d => {{
                    if (d.isCenter) return "YOU";
                    return d.name.split(" ")[0]; // First name only for contacts
                }})
                .style("font-size", d => d.isCenter ? "14px" : "11px")
                .style("font-weight", d => d.isCenter ? "bold" : "normal")
                .style("fill", d => d.isCenter ? "#ffffff" : "#333")
                .style("text-anchor", "middle");

            // Update positions on simulation tick
            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                nodeGroup
                    .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
            }});

            console.log("Graph initialized with", nodes.length, "nodes and", links.length, "links");
        }}

        // Drag functions
        function dragstarted(event, d) {{
            if (d.isCenter) return; // Don't allow dragging center node
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            if (d.isCenter) return; // Don't allow dragging center node
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (d.isCenter) return; // Don't allow dragging center node
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        // Tooltip functions
        function showTooltip(event, d) {{
            if (d.isCenter) {{
                // Special tooltip for center node
                const tooltipContent = `
                    <div class="name">You</div>
                    <div class="detail">Center of your contact network</div>
                `;

                tooltip
                    .html(tooltipContent)
                    .style("opacity", 1);
            }} else {{
                // Regular tooltip for contact nodes
                const tooltipContent = `
                    <div class="name">${{d.name}}</div>
                    ${{d.email ? `<div class="detail">📧 ${{d.email}}</div>` : ''}}
                    ${{d.phone ? `<div class="detail">📞 ${{d.phone}}</div>` : ''}}
                    ${{d.tags && d.tags.length > 0 ? `
                        <div class="tags">
                            ${{d.tags.map(tag => `<span class="tag">${{tag}}</span>`).join('')}}
                        </div>
                    ` : ''}}
                `;

                tooltip
                    .html(tooltipContent)
                    .style("opacity", 1);
            }}

            moveTooltip(event);
        }}

        function moveTooltip(event) {{
            tooltip
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        }}

        function hideTooltip() {{
            tooltip.style("opacity", 0);
        }}

        // Node click handler
        function handleNodeClick(event, d) {{
            console.log("Contact clicked:", d);
            // Future: Open detailed modal
        }}

        // Control functions
        function resetView() {{
            svg.transition()
                .duration(750)
                .call(
                    svg.zoom().transform,
                    d3.zoomIdentity
                );
        }}

        function toggleMode() {{
            isGridMode = !isGridMode;
            const button = event.target;

            if (isGridMode) {{
                // Switch to grid layout
                button.textContent = "Graph View";
                // Future: Implement grid layout
                console.log("Grid mode not yet implemented");
            }} else {{
                // Switch to graph layout
                button.textContent = "Grid View";
                simulation.alpha(1).restart();
            }}
        }}

        // Responsive handling
        function handleResize() {{
            const container = d3.select("#graph");
            const containerNode = container.node();
            const rect = containerNode.getBoundingClientRect();
            const newWidth = rect.width;
            const newHeight = rect.height;

            if (newWidth !== width || newHeight !== height) {{
                width = newWidth;
                height = newHeight;

                svg
                    .attr("width", width)
                    .attr("height", height);

                simulation
                    .force("center", d3.forceCenter(width / 2, height / 2))
                    .alpha(1)
                    .restart();
            }}
        }}

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', () => {{
            initGraph();

            // Handle window resize
            window.addEventListener('resize', handleResize);
        }});

        // Log data for debugging
        console.log('Contact Data:', contactData);
    </script>
</body>
</html>"""

            with open(self.output_path / "index.html", "w", encoding="utf-8") as f:
                f.write(html_content)

            console.print("🎨 Generated interactive D3.js visualization", style="green")
            return True

        except Exception as e:
            console.print(f"❌ Error generating HTML: {e}", style="red")
            return False

    def generate_work_html(self) -> bool:
        """Generate a static grid-based work directory."""
        try:
            export_info = self.export_data["export_info"]
            search_type = export_info["search_type"]
            query = export_info["query"]
            nodes = self.build_nodes()

            cards = []
            for n in nodes:
                email_html = f"<div class='email'>{n['email']}</div>" if n["email"] else ""
                phone_html = f"<div class='phone'>{n['phone']}</div>" if n["phone"] else ""
                cards.append(
                    f"<div class='card'><img src='{n['image_path']}' alt='{n['name']}'><div class='name'>{n['name']}</div>{email_html}{phone_html}</div>"
                )
            cards_html = "\n".join(cards)

            html_content = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Contact Directory - {query}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            margin: 0;
            padding-top: 80px;
        }}
        .header {{
            position: fixed;
            top: 0; left: 0; right: 0;
            background: #fff;
            padding: 20px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 1.5em;
        }}
        .header .search-info {{
            font-size: 0.9em;
            color: #666;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 0 20px 40px;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }}
        .card img {{
            width: 100px;
            height: 100px;
            border-radius: 50%;
            object-fit: cover;
            margin-bottom: 10px;
        }}
        .name {{
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .email, .phone {{
            font-size: 0.9em;
            color: #555;
        }}
    </style>
</head>
<body>
    <div class=\"header\">
        <h1>Contact Directory</h1>
        <div class=\"search-info\">{search_type.title()} search for \"{query}\" • {len(nodes)} contacts</div>
    </div>
    <div class=\"grid\">
        {cards_html}
    </div>
</body>
</html>"""

            with open(self.output_path / "index.html", "w", encoding="utf-8") as f:
                f.write(html_content)

            console.print("🎨 Generated work directory", style="green")
            return True
        except Exception as e:
            console.print(f"❌ Error generating HTML: {e}", style="red")
            return False

    def generate_html(self) -> bool:
        """Generate HTML according to selected layout."""
        if self.layout == "work":
            return self.generate_work_html()
        return self.generate_graph_html()

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
            console.print(
                "⚠️  No contacts found in export data - generating empty directory", style="yellow"
            )

        # Step 4: Create output directory
        if not self.create_output_directory():
            return False

        # Step 5: Copy images
        self.copy_profile_images()

        # Step 6: Generate data file (only for graph layout)
        if self.layout != "work" and not self.generate_data_js():
            return False

        # Step 7: Generate HTML
        if not self.generate_html():
            return False

        # Success!
        success_text = Text()
        success_text.append("✅ Contact directory generated successfully!\n\n", style="bold green")
        success_text.append("📁 Output: ", style="bold")
        success_text.append(f"{self.output_path.absolute()}\n", style="blue")
        success_text.append("🌐 Open: ", style="bold")
        success_text.append(f"file://{self.output_path.absolute()}/index.html\n", style="blue")

        console.print(Panel(success_text, title="Generation Complete", border_style="green"))

        return True


@app.command()
def generate(
    export_dir: str = typer.Argument(..., help="Path to PRT export directory"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory (default: directories/{export_name})"
    ),
    layout: str = typer.Option("graph", "--layout", "-l", help="Layout style: graph or work"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing output directory"),
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
    generator = DirectoryGenerator(export_path, output_path, layout=layout)
    success = generator.generate()

    if not success:
        console.print("❌ Directory generation failed", style="red")
        raise typer.Exit(1)


@app.command()
def info():
    """Show information about make_directory.py."""
    info_text = Text()
    info_text.append("make_directory.py - PRT Contact Directory Generator\n\n", style="bold blue")
    info_text.append(
        "Creates interactive single-page websites from PRT JSON exports.\n", style="white"
    )
    info_text.append("Shows contact relationships as navigable 2D graphs.\n\n", style="white")
    info_text.append("Phase 1: Basic HTML generation with contact cards\n", style="dim")
    info_text.append("Phase 2: D3.js interactive graph visualization (coming soon)\n", style="dim")
    info_text.append("Phase 3: Mobile support and advanced features\n", style="dim")

    console.print(Panel(info_text, title="About", border_style="blue"))


if __name__ == "__main__":
    app()
