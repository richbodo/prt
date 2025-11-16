"""
Export services for PRT CLI.

Pure business logic for exporting search results to various formats.
These functions have minimal UI dependencies and are easily testable.
"""

import copy
import json
from datetime import datetime
from pathlib import Path

from rich.console import Console

# These imports will be done locally to avoid circular dependencies


def export_search_results(
    api, search_type: str, query: str, results: list, *, interactive: bool = True
) -> Path:
    """Export search results to JSON with timestamped folder and optional profile images."""
    console = Console()

    # Create timestamped export directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = Path("exports") / f"{search_type}_search_{timestamp}"
    export_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"📁 Creating export directory: {export_dir}", style="blue")

    # Clean results for JSON serialization (remove binary data)
    clean_results = clean_results_for_json(results)

    # Export JSON data
    export_data = {
        "export_info": {
            "search_type": search_type,
            "query": query,
            "timestamp": timestamp,
            "total_results": len(results),
            "search_request": {"type": search_type, "term": query, "executed_at": timestamp},
        },
        "results": clean_results,
    }

    json_file = export_dir / f"{search_type}_search_results.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    console.print(
        f"💾 Exported {len(results)} {search_type} results to: {json_file}", style="green"
    )

    # Export profile images for contacts
    from .images import export_profile_images_from_results

    images_exported = export_profile_images_from_results(results, export_dir, timestamp)
    if images_exported > 0:
        console.print(f"🖼️  Exported {images_exported} profile images", style="green")

    # Create README for export
    from .directory import create_export_readme

    create_export_readme(export_dir, search_type, query, len(results), images_exported)

    console.print(f"✅ Export complete! Check: {export_dir}", style="bold green")

    # Offer to generate interactive directory (only in interactive mode)
    if interactive:
        from .directory import offer_directory_generation

        offer_directory_generation(export_dir)

    return export_dir


def clean_results_for_json(results: list) -> list:
    """Clean results for JSON serialization by removing binary data."""
    clean_results = copy.deepcopy(results)

    def clean_item(item):
        if isinstance(item, dict):
            # Remove binary data but keep metadata and add image path
            if "profile_image" in item:
                item["has_profile_image"] = item["profile_image"] is not None
                if item["profile_image"] is not None:
                    # Add relative path to exported image
                    item["exported_image_path"] = f"profile_images/{item['id']}.jpg"
                del item["profile_image"]  # Remove binary data

            # Recursively clean nested dictionaries and lists
            for key, value in item.items():
                if isinstance(value, (dict, list)):
                    item[key] = clean_item(value)
        elif isinstance(item, list):
            return [clean_item(x) for x in item]

        return item

    return clean_item(clean_results)
