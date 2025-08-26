# PRT Search Export

## Export Information
- **Search Type**: contacts
- **Query**: "alice"
- **Results**: 1 contacts
- **Profile Images**: 1 exported

## File Structure
```
contacts_search_20250826_182923/
├── README.md                           # This file
├── contacts_search_results.json   # Search results data
└── profile_images/                     # Profile images (if any)
    ├── 1.jpg                          # Contact ID 1's profile image
    ├── 4.jpg                          # Contact ID 4's profile image
    └── ...                            # Additional images
```

## How to Associate Contacts with Images

### Method 1: Using exported_image_path (Recommended)
Each contact in the JSON includes an `exported_image_path` field:
```json
{
  "id": 4,
  "name": "Alice Johnson",
  "exported_image_path": "profile_images/4.jpg",
  "has_profile_image": true
}
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
with open('contacts_search_results.json') as f:
    data = json.load(f)

# Access contact image
for contact in data['results']:
    if contact['has_profile_image']:
        image_path = contact['exported_image_path']
        print(f"{contact['name']}: {image_path}")
```

Generated: 182923
