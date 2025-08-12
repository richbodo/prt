# Personal Relationship Tool (PRT) - MVP Summary

## Purpose
The MVP aims to provide a privacy-first relationship manager that helps a single user maintain meaningful connections. It focuses on secure local storage and quick recall of trusted contacts.

## Scope
- [ ] Command-line interface for early adopters
- [ ] Client-side encrypted contact and relationship database
- [ ] Basic manual search and tagging of relationship qualities - our first-class data
- [ ] Import from personal Google Contacts - our second-class data that we import from elsewhere

## Out of Scope for now
- Web interface or GUI of any kind
- Import from Apple, Facebook, Linkedin, Gmail, Slack, other services.
- Import or annotate communications recency and other qualities as first-class data
- LLM-powered discovery and discussion
- Re-sync Google contacts and merge

## Never Do
- Store data remotely
- Edit contacts - we only edit relationship data
  
## Technical Considerations
- **Typer** for building the CLI experience
- **SQLCipher** or the **cryptography** library to secure the SQLite database
- **LLM Utils** Probably going to try Hugging Face Transformers and openai/gpt-oss-20b
- **Alembic** We'll try do the db right from the start, migrations, backups, etc.

## Functional Breakdown
- [ ] **Secure Storage** – encrypted, local-first contact database
- [ ] **Relationship Tagging** – categorize connections by tags
- [ ] **Search** – find contacts by tag
- [ ] **Import** – Import from a google contacts export

## Success Criteria
- The author successfully uses the tool for day‑to‑day relationship tagging and recall
- Contact data remains private and encrypted 
- Basic import from Google Contacts works
