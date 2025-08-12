# Personal Relationship Tool (PRT) - MVP Summary

## Purpose
The MVP aims to provide a privacy-first relationship manager that helps a single user maintain meaningful connections. It focuses on secure local storage and quick recall of trusted contacts.

## Scope
- Command-line interface for early adopters
- Client-side encrypted contact and relationship database
- Basic search and tagging of relationship qualities - our first-class data
- Import from personal Google Contacts - our second-class data

## Out of Scope
- Web interface or GUI of any kind
- Import from Apple, Facebook, Linkedin, Gmail, Slack, other services.
- Import or annotate communications recency and other qualities as first-class data

## Never Do
- Store data remotely
- Edit contacts 
  
## Technical Considerations
- **Typer** for building the CLI experience
- **SQLCipher** or the **cryptography** library to secure the SQLite database
- 

## Functional Breakdown
1. **Secure Storage** – encrypted, local-first contact database
2. **Relationship Tagging** – categorize connections by tags
3. **Search & Maintenance** – find contacts by tag
4. **Import/Export** – pull from Google and export selected groups when needed

## Success Criteria
- The author successfully uses the tool for day‑to‑day relationship recall
- Contact data remains private and encrypted
- Basic import from Google Contacts works
- Feedback from early adopters informs next development steps
