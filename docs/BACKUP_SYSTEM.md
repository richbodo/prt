# PRT Backup System

**Last Updated:** 2025-01-02
**Status:** Active - Phase 2 (Read-only tools + manual backups)

---

## Overview

PRT implements a comprehensive backup system to protect user data during operations. The backup system is designed to be:
- **Automatic** for all write operations
- **Tracked** with metadata for easy restoration
- **Safe** with pre-operation snapshots
- **Manageable** with cleanup policies for automatic backups

## Backup Philosophy

> **Safety First**: Every write operation creates a backup before modifying data.

The backup system follows these principles:

1. **Non-destructive writes**: Always backup before modification
2. **Transparency**: Users know when backups are created
3. **Traceability**: Every backup has metadata explaining why it was created
4. **Recoverability**: Easy restoration from any backup point

---

## When Backups Are Created

### Automatic Backups (Always Created)

PRT automatically creates backups before these operations:

#### Write Operations on Contacts/Tags/Notes
- Creating new tags
- Creating new notes
- Updating existing notes
- Deleting tags
- Deleting notes
- Adding tags to contacts
- Adding notes to contacts
- Removing tags from contacts
- Removing notes from contacts

#### Relationship Operations
- Creating contact relationships
- Deleting contact relationships
- Bulk relationship operations

#### Direct Database Operations
- Any SQL query with write operations (INSERT, UPDATE, DELETE, ALTER, DROP, etc.)
- Schema migrations

### Manual Backups (User Requested)

Users can create manual backups at any time:
- Via CLI: "Create a backup before I clean up my contacts"
- Via LLM: "Create a backup with comment 'before reorganization'"
- Via API: `api.create_backup_with_comment("my comment")`

---

## Backup Types

### 1. Automatic Backups (`auto=True`)

**Purpose**: Safety backups before write operations
**Naming**: `prt.db.backup_YYYYMMDD_HHMMSS_auto.db`
**Retention**: Keep last 10 automatic backups (configurable)
**Metadata**: Includes operation name that triggered the backup

Example metadata:
```json
{
  "backup_id": 42,
  "timestamp": "2025-01-02T15:30:45",
  "comment": "Auto-backup before: add_tag_to_contact",
  "is_auto": true,
  "original_path": "/path/to/prt.db"
}
```

### 2. Manual Backups (`auto=False`)

**Purpose**: User-initiated safety checkpoints
**Naming**: `prt.db.backup_YYYYMMDD_HHMMSS.db`
**Retention**: Never auto-deleted
**Metadata**: Includes user-provided comment

Example metadata:
```json
{
  "backup_id": 43,
  "timestamp": "2025-01-02T16:00:00",
  "comment": "Manual backup before major cleanup",
  "is_auto": false,
  "original_path": "/path/to/prt.db"
}
```

---

## Backup Storage

### Location

Backups are stored in the `prt_data/backups/` directory:

```
prt_data/
├── prt.db                                    # Active database
└── backups/
    ├── backup_metadata.json                  # Backup tracking metadata
    ├── prt.db.backup_20250102_150000.db     # Manual backup
    ├── prt.db.backup_20250102_153045_auto.db # Auto backup
    └── prt.db.backup_20250102_160000.db     # Manual backup
```

### Metadata Tracking

All backups are tracked in `backup_metadata.json`:

```json
{
  "backups": [
    {
      "backup_id": 42,
      "timestamp": "2025-01-02T15:30:45",
      "backup_path": "/path/to/prt_data/backups/prt.db.backup_20250102_153045_auto.db",
      "comment": "Auto-backup before: add_tag_to_contact",
      "is_auto": true,
      "size_bytes": 1048576,
      "original_path": "/path/to/prt.db"
    },
    {
      "backup_id": 43,
      "timestamp": "2025-01-02T16:00:00",
      "backup_path": "/path/to/prt_data/backups/prt.db.backup_20250102_160000.db",
      "comment": "Manual backup before major cleanup",
      "is_auto": false,
      "size_bytes": 1048576,
      "original_path": "/path/to/prt.db"
    }
  ],
  "next_id": 44
}
```

---

## Using the Backup System

### Creating Backups

#### Via API (Python)
```python
from prt_src.api import PRTAPI

api = PRTAPI()

# Manual backup with comment
backup_info = api.create_backup_with_comment("Before major changes")
print(f"Created backup #{backup_info['backup_id']}")

# Automatic backup before operation (internal use)
backup_info = api.auto_backup_before_operation("bulk_delete_tags")
```

#### Via LLM Chat
```
User: "Create a backup before I reorganize my contacts"
Assistant: [Uses create_backup_with_comment tool]
"✅ Created manual backup #43: 'Before major changes'"
```

#### Via CLI
```bash
# Through interactive CLI
python -m prt_src.cli
# Choose "Manage Database" → "Create Backup"
```

### Viewing Backup History

#### Via API
```python
api = PRTAPI()
backups = api.get_backup_history()

for backup in backups:
    print(f"#{backup['backup_id']}: {backup['timestamp']} - {backup['comment']}")
    print(f"  File: {backup['backup_path']}")
    print(f"  Size: {backup['size_bytes']} bytes")
    print(f"  Auto: {backup['is_auto']}")
```

#### Via LLM Chat
```
User: "Show me my backup history"
Assistant: [Lists recent backups with dates and comments]
```

### Restoring from Backup

#### Via API
```python
api = PRTAPI()

# Restore from backup ID
api.restore_from_backup(backup_id=43)
# This creates a safety backup before restoring!
```

#### Safety Features
- **Pre-restore backup**: Always creates a safety backup before restoring
- **Validation**: Verifies backup file exists and is valid
- **Atomic operation**: Restoration either succeeds completely or fails safely

---

## Cleanup Policies

### Automatic Backup Cleanup

To prevent unlimited backup growth, automatic backups are cleaned up periodically:

**Default Policy**:
- Keep the **10 most recent** automatic backups
- **Never delete** manual backups
- Cleanup runs automatically during backup creation

**Customizing Cleanup**:
```python
api = PRTAPI()

# Keep 20 automatic backups instead of 10
api.cleanup_auto_backups(keep_count=20)

# Or set to 5 for minimal storage
api.cleanup_auto_backups(keep_count=5)
```

### Manual Backup Management

Manual backups are **never automatically deleted**. Users must delete them manually if desired.

**To delete old manual backups**:
1. View backup history: `api.get_backup_history()`
2. Identify backups to remove
3. Delete backup files directly from `prt_data/backups/`
4. Update `backup_metadata.json` (or let system rebuild it)

---

## LLM Tool Integration

### Phase 2 (Current): Read-Only + Manual Backups

**Available LLM Tools**:
- ✅ `create_backup_with_comment` - Create manual backups via chat
- ❌ Write operations - Not yet enabled

Example:
```
User: "Create a backup"
LLM: [Calls create_backup_with_comment]
Assistant: "✅ Created manual backup #43"
```

### Phase 3 (Future): Write Operations

When write tools are enabled, backups will be **automatic**:

```
User: "Tag John as 'friend'"
LLM: [Internally calls auto_backup_before_operation]
LLM: [Then calls add_tag_to_contact]
Assistant: "✅ Tagged John as 'friend' (backup #44 created)"
```

---

## Implementation Details

### Backup Creation Process

1. **Generate backup filename** with timestamp and auto flag
2. **Copy database file** to backup location
3. **Record metadata** in backup_metadata.json:
   - Backup ID (auto-incrementing)
   - Timestamp
   - Comment (operation name or user comment)
   - Auto flag
   - File size
   - Original path
4. **Return backup info** to caller

### Restoration Process

1. **Create safety backup** of current database
2. **Validate backup file** exists and is readable
3. **Stop all database connections** (close sessions)
4. **Copy backup file** over active database
5. **Reconnect to database** with restored data
6. **Verify restoration** succeeded

### Error Handling

**Backup Creation Failures**:
- Insufficient disk space → Log error, operation fails safely
- Permission denied → Log error, operation fails safely
- Corrupted source database → Log error, operation fails safely

**Restoration Failures**:
- Invalid backup ID → Raise ValueError with helpful message
- Backup file not found → Raise FileNotFoundError with path
- Restoration corruption → Safety backup remains, original preserved

---

## Best Practices

### For Users

1. **Create manual backups before major operations**:
   - Mass deletions
   - Bulk imports
   - Schema migrations
   - Data cleanup

2. **Periodically verify backup history**:
   ```python
   api.get_backup_history()  # Check backup count and dates
   ```

3. **Test restoration occasionally**:
   - Restore to a test database to verify backups work
   - Practice recovery procedures

4. **Monitor backup disk usage**:
   - Check `prt_data/backups/` size periodically
   - Adjust automatic backup retention if needed

### For Developers

1. **Always use `auto_backup_before_operation()`** before write operations:
   ```python
   # CORRECT
   api.auto_backup_before_operation("bulk_delete_tags")
   api.bulk_delete_tags(tag_ids)

   # WRONG - No backup!
   api.bulk_delete_tags(tag_ids)
   ```

2. **Provide descriptive operation names** for auto-backups:
   ```python
   api.auto_backup_before_operation("SQL: Update all contact emails")
   ```

3. **Test backup/restore in tests**:
   ```python
   def test_backup_before_write():
       api.create_backup_with_comment("test")
       # Verify backup was created
       backups = api.get_backup_history()
       assert len(backups) > 0
   ```

---

## Future Enhancements

### Planned for Phase 3
- [ ] Compressed backups (gzip) to save disk space
- [ ] Configurable backup retention policies per backup type
- [ ] Backup verification checksums (SHA256)
- [ ] Incremental backups for large databases
- [ ] Remote backup storage options (encrypted)

### Under Consideration
- [ ] Automatic backup on PRT startup
- [ ] Scheduled backups (daily/weekly)
- [ ] Backup encryption with user key
- [ ] Backup restoration preview (what changes will occur)
- [ ] Backup diff tool (compare two backups)

---

## Troubleshooting

### "Backup creation failed: Permission denied"

**Cause**: Insufficient permissions to write to `prt_data/backups/`
**Solution**:
```bash
chmod 750 prt_data/backups/
```

### "Restoration failed: Backup file not found"

**Cause**: Backup file was manually deleted or moved
**Solution**: Check `prt_data/backups/` for available backups, update metadata if needed

### "Too many automatic backups, disk space low"

**Cause**: Automatic backup retention is too high
**Solution**:
```python
api.cleanup_auto_backups(keep_count=5)  # Reduce to 5 most recent
```

### "Backup restoration broke my database"

**Cause**: Corrupted backup file
**Solution**:
1. Check the safety backup created before restoration
2. Restore from the safety backup
3. Verify backup file integrity before restoring again

---

## References

### Code Files
- `prt_src/api.py` - Backup API methods
- `prt_src/db.py` - Low-level backup operations
- `prt_src/llm_ollama.py` - LLM tool integration (future write ops)

### Related Documentation
- `docs/DB_MANAGEMENT.md` - Database management guide
- `docs/LLM_Integration/README.md` - LLM tool integration details
- `CLAUDE.md` - Development patterns and error handling

---

## Changelog

### 2025-01-02 - Initial Version
- Documented automatic backup before writes
- Documented manual backup creation
- Documented cleanup policies
- Added LLM tool integration notes
- Added troubleshooting section
