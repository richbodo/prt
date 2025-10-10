# Manual Testing Guide - Phase 1

**Date:** October 10, 2025
**Status:** Testing with all 15 tools
**Branch:** restore_old_llm_code

## Quick Start

```bash
# Option 1: Use test script (recommended)
python test_llm_manual.py

# Option 2: Use CLI directly
python -m prt_src.cli chat

# Option 3: Use interactive CLI menu
python -m prt_src.cli
# Then select "Start Chat"
```

## Test Queries

Try these queries in order and note results:

### Basic Queries (Should work well)
1. ✅ "Show me all contacts"
2. ✅ "Find contacts named John"
3. ✅ "How many contacts do I have?"
4. ✅ "What tags do I have?"

### Specific Queries (Test tool selection)
5. ✅ "What's Alice's email?"
6. ✅ "Tell me about contact #5"
7. ✅ "Who works at Google?"
8. ✅ "Find notes about meetings"

### Conversational Queries (Test natural language understanding)
9. ✅ "Show me everyone"
10. ✅ "Who do I know in tech?"
11. ✅ "People in San Francisco"

### Non-tool Queries (Should answer directly)
12. ✅ "What is PRT?"
13. ✅ "How do I add a tag?"
14. ✅ "What can you do?"

### Edge Cases (Expected to handle gracefully)
15. ✅ "Find contact XYZ123" (non-existent)
16. ✅ "Show me tag FOOBAR" (non-existent)
17. ✅ "" (empty query)

## What to Document

For each query, note:
- ✅ **Tool selection**: Did it pick the right tool?
- ✅ **Parameters**: Were the parameters correct?
- ✅ **Results**: Did it return useful data?
- ✅ **Response**: Was the LLM's response helpful?
- ❌ **Errors**: Any failures or unexpected behavior?

## Current Tool List (All 15)

The system has these tools available:

**Read-only (queries):**
1. `search_contacts(query)` - Search by name, email, etc.
2. `list_all_contacts()` - Get all contacts
3. `get_contact_details(contact_id)` - Get specific contact
4. `search_tags(query)` - Search tags
5. `list_all_tags()` - Get all tags
6. `get_contacts_by_tag(tag_name)` - Contacts with specific tag
7. `search_notes(query)` - Search notes
8. `list_all_notes()` - Get all notes
9. `get_contacts_by_note(note_title)` - Contacts with specific note
10. `get_database_stats()` - Get database statistics

**Write operations:**
11. `add_tag_to_contact(contact_id, tag_name)` - Add tag
12. `add_note_to_contact(contact_id, note_title, note_content)` - Add note
13. `create_tag(name)` - Create new tag
14. `create_note(title, content)` - Create new note

**Advanced:**
15. `execute_sql(sql, confirm)` - Direct SQL execution (requires confirm=true)
16. `create_backup_with_comment(comment)` - Create backup

## Expected Behavior

**Good signs:**
- ✅ LLM selects appropriate tools
- ✅ Parameters are reasonable
- ✅ Results are formatted helpfully
- ✅ Conversation flows naturally
- ✅ Errors are handled gracefully

**Red flags (note these):**
- ❌ Wrong tool selected
- ❌ Malformed parameters
- ❌ LLM makes up data instead of using tools
- ❌ Crashes or hangs
- ❌ Confusing or unhelpful responses

## Known Issues (Will discover during testing)

*Document issues here as you find them*

## Performance Notes

First query may be slow (20-40 seconds) if model needs to load.
Subsequent queries should be faster (5-15 seconds).

## After Testing

Create a summary:
- What worked well?
- What needs improvement?
- Do we need all 15 tools or can we simplify?
- Any bugs to fix before Phase 2?

Update: docs/LLM_Integration/Phase1_Results.md
