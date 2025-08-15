# Database Schema Plan

This document outlines the proposed schema for PRT.

## Reference

The latest Google Contacts download schema is available on GitHub:
<https://developers.google.com/people/api/rest/v1/people#Person>

## Proposed Superset Schema

The PRT schema extends Google Contacts by adding dedicated tables to track relationship metadata.

### Core Tables

- **contacts** – stores imported Google Contacts fields (name, email, etc.) along with any additional attributes.
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
