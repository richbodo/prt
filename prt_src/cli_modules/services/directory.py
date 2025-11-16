"""
Directory generation services for PRT CLI.

Functions for creating interactive directories from exports and managing README files.
These functions handle the integration with the make_directory.py tool.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt


def offer_directory_generation(export_dir: Path) -> None:
    """Offer to generate an interactive directory from the export."""
    console = Console()

    console.print()

    # Ask user if they want to generate interactive directory
    generate = Prompt.ask(
        "🌐 Generate interactive directory from this export?", choices=["y", "n"], default="y"
    )

    if generate == "y":
        try:
            # Create directories subdirectory in the project root
            directories_dir = Path("directories")
            directories_dir.mkdir(exist_ok=True)

            # Generate timestamp-based output directory name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = directories_dir / f"directory_{timestamp}"

            console.print("🔧 Generating interactive directory...", style="blue")

            # Run make_directory.py tool
            tools_dir = Path(__file__).parent.parent.parent / "tools"
            make_directory_script = tools_dir / "make_directory.py"

            # Run the command - pass the export directory, not the JSON file
            cmd = [
                sys.executable,
                str(make_directory_script),
                "generate",
                str(export_dir),
                "--output",
                str(output_dir),
                "--force",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

            if result.returncode == 0:
                # Success! Show the local file URL
                index_file = output_dir / "index.html"
                if index_file.exists():
                    file_url = f"file://{index_file.absolute()}"
                    console.print("✅ Interactive directory generated!", style="bold green")
                    console.print(f"🌐 Open in browser: {file_url}", style="blue")
                    console.print(f"📁 Directory location: {output_dir}", style="dim")
                else:
                    console.print(f"✅ Directory generated at: {output_dir}", style="green")
            else:
                console.print(f"❌ Error generating directory: {result.stderr}", style="red")

        except Exception as e:
            console.print(f"❌ Error running make_directory tool: {e}", style="red")

    console.print()


def create_export_readme(
    export_dir: Path, search_type: str, query: str, result_count: int, image_count: int
) -> None:
    """Create a README file explaining the export structure."""
    readme_content = f"""# PRT Search Export

## Export Information
- **Search Type**: {search_type}
- **Query**: "{query}"
- **Results**: {result_count} {search_type}
- **Profile Images**: {image_count} exported

## File Structure
```
{export_dir.name}/
├── README.md                           # This file
├── {search_type}_search_results.json   # Search results data
└── profile_images/                     # Profile images (if any)
    ├── 1.jpg                          # Contact ID 1's profile image
    ├── 4.jpg                          # Contact ID 4's profile image
    └── ...                            # Additional images
```

## How to Associate Contacts with Images

### Method 1: Using exported_image_path (Recommended)
Each contact in the JSON includes an `exported_image_path` field:
```json
{{
  "id": 4,
  "name": "Alice Johnson",
  "exported_image_path": "profile_images/4.jpg",
  "has_profile_image": true
}}
```

### Method 2: Using Contact ID
Profile images are named using the contact ID:
- Contact ID 1 → `profile_images/1.jpg`
- Contact ID 4 → `profile_images/4.jpg`

## JSON Fields Explained
- `has_profile_image`: Boolean indicating if contact has a profile image
- `exported_image_path`: Relative path to the exported image file
- `profile_image_filename`: Original filename from the database
- `profile_image_mime_type`: Image format (e.g., "image/jpeg")

## Usage Examples
```python
import json

# Load the JSON data
with open('{search_type}_search_results.json') as f:
    data = json.load(f)

# Access contact image
for contact in data['results']:
    if contact['has_profile_image']:
        image_path = contact['exported_image_path']
        print(f"{{contact['name']}}: {{image_path}}")
```

Generated: {export_dir.name.split('_')[-1]}
"""

    readme_file = export_dir / "README.md"
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme_content)
