# Database Schema Plan

This document outlines the proposed schema for PRT.

## Reference

The latest Google Contacts download schema is available on GitHub:
<https://developers.google.com/people/api/rest/v1/people#Person>

## Proposed Superset Schema

The PRT schema extends Google Contacts by adding dedicated tables to track relationship metadata.

- **contacts** – stores imported Google Contacts fields (name, email, etc.) along with any additional attributes.
- **tags** – editable list of tag names.
- **relationships** – links a contact to multiple tags and notes.
- **relationship_tags** – many‑to‑many join table between relationships and tags.
- **notes** – free‑form notes associated with a relationship.

This design supports unlimited tags and notes per relationship while remaining compatible with Google Contacts fields.
