# Personal Relationship Tool (PRT) - MVP Summary

## Purpose
The MVP aims to provide a privacy-first relationship manager that helps a single user maintain meaningful connections. It focuses on secure local storage and quick recall of trusted contacts.

## Scope
- Command-line interface for early adopters
- Client-side encrypted contact and relationship database
- Basic search and tagging by relationship qualities
- Optional import from personal Google Contacts

## Out of Scope
- Public feeds or push notifications
- Cloud-based storage without encryption
- Advertising or data monetization
- Complex social networking features

## Technical Considerations
- **Typer** for building the CLI experience
- **LangChain** for future AI-assisted workflows
- **google-api-python-client** for contact import
- **SQLCipher** or the **cryptography** library to secure the SQLite database

## Functional Breakdown
1. **Secure Storage** – encrypted, local-first contact database
2. **Relationship Tagging** – categorize connections by trust, recency, and custom tags
3. **Search & Maintenance** – find contacts by tag and list those not contacted recently
4. **Import/Export** – pull from Google and export selected groups when needed

## Success Criteria
- The author successfully uses the tool for day‑to‑day relationship recall
- Contact data remains private and encrypted
- Basic import from Google Contacts works
- Feedback from early adopters informs next development steps
