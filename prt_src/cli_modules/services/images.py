"""
Image export services for PRT CLI.

Functions for handling profile image exports from search results.
These functions have minimal UI dependencies and are easily testable.
"""

from pathlib import Path

from rich.console import Console


def export_profile_images_from_results(results: list, export_dir: Path, timestamp: str) -> int:
    """Export profile images from any result structure (contacts, tags with contacts, notes with contacts)."""
    console = Console()

    images_dir = export_dir / "profile_images"
    images_dir.mkdir(exist_ok=True)

    images_exported = 0
    contacts_to_process = []

    # Extract contacts from different result structures
    for result in results:
        if "associated_contacts" in result:
            # Tag or note search results
            contacts_to_process.extend(result["associated_contacts"])
        elif "id" in result and "name" in result:
            # Direct contact search results
            contacts_to_process.append(result)

    # Export images for all found contacts
    for contact in contacts_to_process:
        if contact.get("profile_image"):
            try:
                # Generate filename: contact_id.jpg
                contact_id = contact["id"]
                filename = f"{contact_id}.jpg"

                # Save image data
                image_path = images_dir / filename
                with open(image_path, "wb") as f:
                    f.write(contact["profile_image"])
                images_exported += 1

            except Exception as e:
                console.print(
                    f"Warning: Failed to export image for contact {contact['id']}: {e}",
                    style="yellow",
                )

    return images_exported


def export_contact_profile_images(api, contacts: list, export_dir: Path, timestamp: str) -> int:
    """Export profile images for contacts. (Deprecated - use export_profile_images_from_results)"""
    return export_profile_images_from_results(contacts, export_dir, timestamp)
