# Quick Start: LLM Tools

**Status:** ✅ 24 tools operational with advanced features
**Last Updated:** 2025-01-02

---

## Launch TUI with LLM Chat

```bash
python -m prt_src.tui
# Press 'c' to open Chat screen
```

---

## What You Can Ask

### Find Information (Read-Only)
```
"How many contacts do I have?"
"Find contacts named John"
"Show me all my tags"
"Who is tagged as 'family'?"
"Search for notes about meetings"
"Tell me about contact #5"
```

### Modify Data (Auto-Backup Before Each Operation)
```
"Tag John as 'friend'"
"Remove the 'work' tag from Sarah"
"Create a new tag called 'colleagues'"
"Add a note to contact #1 about our meeting"
"Update the 'Birthday' note with new date"
"Delete the 'old-contacts' tag"
```

### Manual Backups
```
"Create a backup before I reorganize"
"Make a backup with comment 'Before cleanup'"
```

### SQL Queries (NEW in Phase 4)
```
"Find all contacts without email addresses"
"How many contacts have more than 3 tags?"
"Show me contacts created in the last month"
```
**Note:** ALL SQL queries require user confirmation before executing.

### Directory Visualization (NEW in Phase 4)
```
"Generate a visualization of my family contacts"
"Create an interactive directory of work colleagues"
"Show me a network graph of all contacts"
```
**Note:** Creates D3.js visualization with profile images.

### Relationship Management (NEW in Phase 4)
```
"Link Alice and Bob as friends"
"Mark John as Sarah's parent"
"Remove the colleague relationship between Alice and Bob"
```
**Note:** Automatic backups created before modifying relationships.

---

## Safety Features

✅ **Automatic backups** before every write operation
✅ **Backup ID in response**: "Tagged John (backup #42 created)"
✅ **No data loss** - backup exists even if operation fails
✅ **Restore capability** - all backups tracked in metadata

**Backups stored in:** `prt_data/backups/`
**Metadata tracked in:** `prt_data/backups/backup_metadata.json`

---

## Available Tools (24 Total)

**Read-Only (10):**
- search_contacts, list_all_contacts, get_contact_details
- list_all_tags, search_tags, get_contacts_by_tag
- list_all_notes, search_notes, get_contacts_by_note
- get_database_stats

**Write - Tags (4):**
- add_tag_to_contact, remove_tag_from_contact
- create_tag, delete_tag

**Write - Notes (5):**
- add_note_to_contact, remove_note_from_contact
- create_note, update_note, delete_note

**Utility (1):**
- create_backup_with_comment

**Advanced - Phase 4 (4):**
- execute_sql (requires confirmation for ALL queries)
- generate_directory (creates D3.js visualizations)
- add_contact_relationship (links contacts with backups)
- remove_contact_relationship (removes links with backups)

---

## Testing

```bash
# Run all integration tests
./prt_env/bin/pytest tests/integration/test_llm_write_tools.py -v

# Test specific write operation
./prt_env/bin/pytest tests/integration/test_llm_write_tools.py::TestLLMWriteTools::test_add_tag_creates_backup -xvs
```

**All tests passing:** 14 write tool tests + 5 API tests = 19 tests ✅

---

## Documentation

- **BACKUP_SYSTEM.md** - How backups work
- **PHASE2_COMPLETE.md** - Read-only tools (Phase 2)
- **PHASE3_COMPLETE.md** - Write operations (Phase 3)
- **LLM_Integration/README.md** - Complete overview

---

## Next: Manual Testing Checklist

1. Launch TUI: `python -m prt_src.tui`
2. Open Chat (press 'c')
3. Test read operations (search, list, get)
4. Test write operations (create, add, update, delete)
5. Verify backups created in `prt_data/backups/`
6. Check backup metadata shows operation names
7. Test manual backup creation
8. Verify LLM responses include backup IDs

---

**Status:** Production ready - all 24 tools tested and operational! 🎉

**Phase 4 Highlights:**
- SQL tool for complex queries (requires confirmation)
- Directory generation with D3.js visualizations
- Relationship management between contacts
- All Phase 4 tools tested with 11 integration tests
