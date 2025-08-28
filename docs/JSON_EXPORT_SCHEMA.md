# PRT JSON Export Schema Documentation

This document defines the standardized JSON export format used by PRT's search and export functionality. This schema is critical for Issue #40 (single-page directory creator) and future export-based tools.

## Overview

PRT exports search results in a consistent JSON format with associated profile images. Each export creates:
- A timestamped directory (e.g., `contacts_search_20250826_182923/`)
- A JSON file with search results
- A `profile_images/` directory with contact images
- A `README.md` file with usage instructions

## JSON Schema Structure

### Top-Level Schema

```json
{
  "export_info": {
    "search_type": "contacts|tags|notes",
    "query": "search_term",
    "timestamp": "20250826_182923",
    "total_results": 5,
    "search_request": {
      "type": "contacts|tags|notes",
      "term": "search_term",
      "executed_at": "20250826_182923"
    }
  },
  "results": [
    // Array of result objects (structure depends on search_type)
  ]
}
```

### Export Info Fields

| Field | Type | Description |
|-------|------|-------------|
| `search_type` | string | Type of search: "contacts", "tags", or "notes" |
| `query` | string | The search term used |
| `timestamp` | string | Export timestamp in YYYYMMDD_HHMMSS format |
| `total_results` | integer | Number of results in the export |
| `search_request` | object | Detailed search request information |

### Search Request Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Search type (same as search_type) |
| `term` | string | Search term (same as query) |
| `executed_at` | string | Timestamp when search was executed |

## Result Structures by Search Type

### Contact Search Results

```json
{
  "results": [
    {
      "id": 4,
      "name": "Alice Johnson",
      "email": "alice.johnson@gmail.com",
      "phone": "+1-555-0104",
      "profile_image_filename": "alice_johnson.jpg",
      "profile_image_mime_type": "image/jpeg",
      "has_profile_image": true,
      "exported_image_path": "profile_images/4.jpg",
      "relationship_info": {
        "tags": ["friend", "neighbor"],
        "notes": [
          {
            "title": "First Meeting",
            "content": "Met at the coffee shop downtown..."
          }
        ]
      }
    }
  ]
}
```

### Tag Search Results

```json
{
  "results": [
    {
      "tag": {
        "id": 2,
        "name": "friend",
        "contact_count": 3
      },
      "associated_contacts": [
        {
          "id": 4,
          "name": "Alice Johnson",
          "email": "alice.johnson@gmail.com",
          "phone": "+1-555-0104",
          "profile_image_filename": "alice_johnson.jpg",
          "profile_image_mime_type": "image/jpeg",
          "has_profile_image": true,
          "exported_image_path": "profile_images/4.jpg",
          "relationship_info": {
            "tags": ["friend", "neighbor"],
            "notes": [...]
          }
        }
      ]
    }
  ]
}
```

### Note Search Results

```json
{
  "results": [
    {
      "note": {
        "id": 1,
        "title": "First Meeting",
        "content": "Met at the coffee shop downtown..."
      },
      "associated_contacts": [
        {
          "id": 4,
          "name": "Alice Johnson",
          // ... same contact structure as above
        }
      ]
    }
  ]
}
```

## Contact Object Schema

All contact objects (regardless of search type) follow this structure:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | Yes | Unique contact identifier |
| `name` | string | Yes | Contact's full name |
| `email` | string | No | Primary email address (may be null) |
| `phone` | string | No | Primary phone number (may be null) |
| `profile_image_filename` | string | No | Original filename of profile image |
| `profile_image_mime_type` | string | No | MIME type (e.g., "image/jpeg") |
| `has_profile_image` | boolean | Yes | Whether contact has a profile image |
| `exported_image_path` | string | Conditional | Relative path to exported image (only if has_profile_image=true) |
| `relationship_info` | object | Yes | Tags and notes associated with contact |

### Relationship Info Schema

```json
{
  "relationship_info": {
    "tags": ["tag1", "tag2"],
    "notes": [
      {
        "title": "Note Title",
        "content": "Note content..."
      }
    ]
  }
}
```

## Profile Images

### Image File Naming
- Images are saved as `{contact_id}.jpg` in the `profile_images/` directory
- Example: Contact ID 4 → `profile_images/4.jpg`

### Image Association
**Method 1 (Recommended)**: Use the `exported_image_path` field
```json
{
  "id": 4,
  "exported_image_path": "profile_images/4.jpg"
}
```

**Method 2**: Map contact ID to filename
- Contact ID 4 → `profile_images/4.jpg`

### Image Properties
- Format: JPEG
- Naming: `{contact_id}.jpg`
- Size: Varies (typically 256x256 pixels for generated images)
- Location: Always in `profile_images/` subdirectory

## Data Integrity Guarantees

### JSON Serialization
- All binary data is removed from JSON (no `profile_image` field)
- Image metadata is preserved (`profile_image_filename`, `profile_image_mime_type`)
- Images are exported separately to maintain JSON readability

### Consistency Rules
1. If `has_profile_image` is `true`, `exported_image_path` will be present
2. If `exported_image_path` is present, the corresponding image file exists
3. All timestamps use YYYYMMDD_HHMMSS format
4. Contact IDs are unique within an export
5. Image filenames follow the `{contact_id}.jpg` pattern

## Usage Examples

### Python: Loading Export Data

```python
import json
from pathlib import Path

# Load export
export_dir = Path("exports/contacts_search_20250826_182923")
with open(export_dir / "contacts_search_results.json") as f:
    data = json.load(f)

# Access export metadata
search_info = data["export_info"]
print(f"Search: {search_info['search_type']} for '{search_info['query']}'")
print(f"Found: {search_info['total_results']} results")

# Process contacts
for contact in data["results"]:
    print(f"Contact: {contact['name']}")
    if contact["has_profile_image"]:
        image_path = export_dir / contact["exported_image_path"]
        print(f"  Image: {image_path}")
```

### JavaScript: Processing in Browser

```javascript
// Load JSON (assuming it's been loaded via fetch or file input)
const exportData = JSON.parse(jsonString);

// Create image elements for contacts
exportData.results.forEach(contact => {
    if (contact.has_profile_image) {
        const img = document.createElement('img');
        img.src = contact.exported_image_path;
        img.alt = contact.name;
        // Add to DOM...
    }
});
```

## Compatibility Notes

### Issue #40 Requirements
This schema is designed to support Issue #40's directory creator tool:
- ✅ **Fixed JSON format**: Consistent structure across all search types
- ✅ **Consistent filesystem format**: Predictable directory structure
- ✅ **Image association**: Multiple methods to link contacts to images
- ✅ **Relationship data**: Tags and notes included for graph visualization
- ✅ **Search context**: Full search request preserved for tool reference

### Future Extensibility
The schema supports future enhancements:
- Additional contact fields can be added without breaking existing tools
- New search types can be added with their own result structures
- Export metadata can be extended with additional information
- Image formats beyond JPEG can be supported

## Migration and Versioning

Currently, this is the initial schema version. Future changes will:
1. Maintain backward compatibility where possible
2. Add schema version field if breaking changes are needed
3. Provide migration tools for existing exports
4. Document all changes in this file

---

**Last Updated**: August 26, 2025
**Schema Version**: 1.0
**Related Issues**: #19 (Search Export), #40 (Directory Creator)
