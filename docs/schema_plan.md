# Database Schema Plan

This document outlines the proposed schema for PRT.

## Reference

The latest Google Contacts download schema is available on GitHub:
<https://developers.google.com/people/api/rest/v1/people#Person>

## Proposed Superset Schema

The PRT schema extends Google Contacts by adding dedicated tables to track relationship metadata.

### Core Tables

- **contacts** – stores imported contact information with support for profile images:
  - Basic fields: name, email, phone
  - Profile image fields: image data (binary), filename, MIME type
  - Import source: Google Contacts CSV or Google Takeout (with images)
- **relationships** – links a contact to multiple tags and notes (one-to-one with contacts).
- **tags** – editable list of tag names that can be applied to relationships.
- **relationship_tags** – many‑to‑many join table between relationships and tags.
- **notes** – free‑form notes with titles that can be associated with relationships.
- **relationship_notes** – many‑to‑many join table between relationships and notes.

### Key Design Principles

- **One relationship per contact** - Each contact has exactly one relationship record
- **Multiple tags per relationship** - Relationships can have multiple descriptive tags
- **Multiple notes per relationship** - Relationships can have multiple notes
- **Reusable tags and notes** - Tags and notes are shared across relationships (e.g., "friend" tag, "Meeting notes from widget proposal" note)
- **Searchable notes** - Notes have titles for easy identification and searching

### Example Usage

```
Contact: John Doe
Relationship: 
  Tags: friend, colleague, mentor
  Notes: 
    - "College memories" - Met at college in 2010
    - "Career advice" - Great advice on career decisions

Contact: Alice Smith
Relationship:
  Tags: friend, colleague
  Notes:
    - "Meeting notes from widget proposal" - Discussed new project ideas
    - "Career advice" - Great advice on career decisions (same note as John)
```

This design supports unlimited tags and notes per relationship while remaining compatible with Google Contacts fields.

## Schema Evolution

### Version 1 (Initial)
- Basic contact storage: name, email, phone
- Relationship management with tags and notes
- Google Contacts CSV import support

### Version 2 (Current)
- **Profile Image Support**: Added fields for storing contact profile pictures
  - `profile_image`: Binary image data stored directly in database
  - `profile_image_filename`: Original filename for reference
  - `profile_image_mime_type`: MIME type (e.g., 'image/jpeg')
- **Google Takeout Import**: Import contacts with images from Google Takeout zip files
- **Safe Migration System**: Automatic backup and recovery for schema changes

### Future Considerations
- Additional contact fields (address, organization, etc.)
- Image optimization and compression
- Support for multiple images per contact
- Integration with other contact sources

## Migration Management

PRT uses a simple schema versioning system that prioritizes data safety:

- **Automatic Detection**: System detects current schema version
- **Safe Upgrades**: Creates backup before any schema changes
- **Recovery Instructions**: Clear guidance if migration fails
- **User Control**: Users can always restore from backup

See [Database Management Guide](DB_MANAGEMENT.md#database-schema-migrations) for detailed migration procedures.
