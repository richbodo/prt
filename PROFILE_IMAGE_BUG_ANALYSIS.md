# Profile Image Storage and JSON Serialization Bug - Complete Analysis

## EXECUTIVE SUMMARY

The bug occurs when the `execute_sql` tool returns query results containing profile images (binary data). These results are then passed through `json.dumps()` on line 1339 of `llm_ollama.py`, which fails because binary data cannot be directly serialized to JSON. While a `_json_serializer` exists to handle this, it's only used for tool results in the conversation history, not for the logging that crashes the execution.

## 1. PROFILE IMAGE STORAGE IN DATABASE

### Database Schema (models.py, lines 28-78)

**Contact Model** stores three profile image-related columns:
```python
profile_image = Column(LargeBinary)                    # Binary image data (JPG, PNG, etc.)
profile_image_filename = Column(String(255))           # Original filename (e.g., "john.jpg")
profile_image_mime_type = Column(String(50))           # MIME type (e.g., "image/jpeg")
```

### Storage Characteristics:
- **Type**: `LargeBinary` - SQLite stores as BLOB (Binary Large Object)
- **Content**: Raw binary image file data (not base64 encoded in database)
- **Size**: Variable, typically 50KB-500KB per image for JPEG/PNG
- **Format**: Any format SQLAlchemy can store (JPEG, PNG, GIF, etc.)

### Example Data Flow (from db.py):
```python
# Line 322-334: Inserting contact with profile image
profile_image = contact_data.get("profile_image")          # Binary data
profile_image_filename = contact_data.get("profile_image_filename")
profile_image_mime_type = contact_data.get("profile_image_mime_type")

contact = Contact(
    name=name,
    email=emails[0] if emails else None,
    profile_image=profile_image,                          # Stored as binary blob
    profile_image_filename=profile_image_filename,
    profile_image_mime_type=profile_image_mime_type,
)
```

## 2. API LAYER RESPONSE HANDLING (api.py)

### Where Profile Images Are Returned

The API returns profile images in multiple methods. Example from `search_contacts()` (lines 294-317):

```python
def search_contacts(self, query: str) -> List[Dict[str, Any]]:
    contacts = (
        self.db.session.query(Contact)
        .filter(Contact.name.ilike(f"%{query}%"))
        .order_by(Contact.name)
        .all()
    )
    
    return [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "profile_image": c.profile_image,              # ← BINARY DATA RETURNED HERE
            "profile_image_filename": c.profile_image_filename,
            "profile_image_mime_type": c.profile_image_mime_type,
            "relationship_info": self.get_relationship_info(c.id),
        }
        for c in contacts
    ]
```

### Other Methods Returning Profile Images:
1. **`list_all_contacts()`** (lines 709-726) - Returns all contacts with profile_image
2. **`get_contact_details()`** (lines 690-707) - Returns single contact with profile_image
3. **`get_contacts_by_tag()`** (lines 481-505) - Returns contacts with profile_image
4. **`get_contacts_by_note()`** (lines 507-531) - Returns contacts with profile_image
5. **`execute_sql()`** (lines 162-210) - Returns raw query results as dicts, potentially including profile_image if queried

### The execute_sql Problem (api.py, lines 191-196):

```python
try:
    res = self.db.session.execute(text(sql))
    if res.returns_rows:
        rows = [dict(row._mapping) for row in res]    # ← Line 194: Returns all columns including binary
        result["rows"] = rows
        result["rowcount"] = len(rows)
```

**Critical Issue**: When a SELECT query includes the `profile_image` column, `dict(row._mapping)` returns a dictionary with the binary data intact. This result is then returned to the LLM tool, which attempts to JSON serialize it.

## 3. JSON SERIALIZATION PROBLEM IN llm_ollama.py

### Problem Location 1: Logging Tool Results (Line 1339)

```python
if tool_name == "execute_sql":
    logger.info(f"[LLM] Tool {tool_name} FULL result: {json.dumps(tool_result, indent=2)}")
    # ↑ CRASHES HERE if tool_result contains binary data
else:
    logger.debug(f"[LLM] Tool {tool_name} result: {str(tool_result)[:200]}")
```

**Why it crashes**: `json.dumps()` is called WITHOUT the `default=self._json_serializer` parameter for execute_sql tool logging.

### Problem Location 2: Storing in Conversation History (Lines 1354-1363)

```python
for tool_result in tool_results:
    self.conversation_history.append(
        {
            "role": "tool",
            "tool_call_id": tool_result["tool_call_id"],
            "content": json.dumps(
                tool_result["result"], default=self._json_serializer  # ← Has serializer here
            ),
        }
    )
```

**This one is PROTECTED**: Uses `default=self._json_serializer` parameter.

### The _json_serializer Method (Lines 1486-1501)

```python
def _json_serializer(self, obj):
    """Custom JSON serializer to handle non-serializable objects like bytes."""
    if isinstance(obj, bytes):
        return f"<binary data: {len(obj)} bytes>"
    elif hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    else:
        return str(obj)
```

**Function**: Converts bytes to a string representation instead of trying to serialize binary data directly.

## 4. PROBLEM PROPAGATION PATH

```
User Query
    ↓
LLM calls execute_sql tool with SQL: "SELECT * FROM contacts LIMIT 1"
    ↓
execute_sql (api.py) executes SQL
    ↓
Result contains profile_image column as bytes
    ↓
Result dict returned to llm_ollama.py _call_tool()
    ↓
Line 1339: logger.info(...json.dumps(tool_result, indent=2))
    ↓
json.dumps() encounters bytes object
    ↓
TypeError: Object of type bytes is not JSON serializable
    ↓
Exception raised, tool execution fails
    ↓
LLM receives error instead of results
```

## 5. WHY PROFILE IMAGES ARE INCLUDED IN QUERY RESULTS

### Design Decision:
The API methods are designed to return complete contact objects. Profile images are:
- Part of the Contact model
- Needed by UI/visualization tools (make_directory.py)
- Automatically included in all contact queries

### Specific Case - execute_sql:
When user runs: `SELECT * FROM contacts WHERE id=1`
- Result includes ALL columns, including profile_image as binary data
- execute_sql cannot know which columns are binary without schema inspection
- Result is returned as-is (dict of row values)

## 6. WHERE THE FIX IS NEEDED

### Location 1: execute_sql in api.py (CRITICAL)
**Lines 191-196**: Filter out binary columns or handle serialization
```python
if res.returns_rows:
    rows = [dict(row._mapping) for row in res]
    # ← Should sanitize binary columns here
    result["rows"] = rows
```

### Location 2: llm_ollama.py Line 1339 (CRITICAL)
**Execute_sql Tool Logging**: Add serializer parameter
```python
if tool_name == "execute_sql":
    logger.info(f"[LLM] Tool {tool_name} FULL result: {json.dumps(tool_result, indent=2, default=self._json_serializer)}")
    # ↑ Add default=self._json_serializer
```

### Location 3: Directory Generation (ALREADY FIXED)
**Lines 840-862**: Shows the correct pattern
```python
for contact in clean_contacts:
    if contact.get("profile_image"):
        # Export to file
        with open(image_file, "wb") as f:
            f.write(contact["profile_image"])
        # Mark that image exists
        contact["has_profile_image"] = True
        # Remove binary data before JSON serialization
        del contact["profile_image"]  # ← KEY STEP
```

## 7. RELATED CODE PATTERNS

### Correct Pattern in Directory Generation (llm_ollama.py, lines 844-862):
The code CORRECTLY handles profile images for directory generation:
1. Exports binary data to files (not in JSON)
2. Removes binary data from objects before JSON serialization
3. Stores path to the exported image file instead

This is the pattern that should be followed for ALL binary data handling.

### Incomplete Pattern in API Response Methods:
The `search_contacts()`, `list_all_contacts()`, etc. methods return profile_image in the dict. These are fine for:
- TUI display (which handles binary)
- Directory generation (which removes it before JSON)
- But NOT for execute_sql results that go to LLM (which need JSON serialization)

## 8. BYTE LIMITS AND SIZE CONSIDERATIONS

### Profile Image Size in Database:
- Typical profile image: 50-500 KB
- SQLite BLOB storage: No size limit per column, but database has practical limits
- Memory impact: Each profile image loaded in Python is stored in memory

### Impact on execute_sql:
When querying 100 contacts with profile images:
- 100 × 200 KB = 20 MB of binary data
- Attempting to json.dumps() this will fail
- String representation overhead: Each image becomes `<binary data: 200000 bytes>` (27 bytes + len of byte count)

## 9. TEST FILE REFERENCES

### test_execute_sql.py:
Only has 3 basic tests, none test profile_image scenarios:
- `test_execute_sql_read_only_returns_rows` - Simple name query, no profile_image
- `test_execute_sql_write_requires_confirmation` - Delete operation
- `test_execute_sql_backup_before_write` - Update operation

### Fixtures (tests/fixtures.py):
Uses `generate_profile_images()` to create binary profile image data for test contacts.

## 10. COMPLETE DATA FLOW SUMMARY

```
STORAGE LAYER (models.py)
├── Contact.profile_image: LargeBinary column
├── Contact.profile_image_filename: String column
└── Contact.profile_image_mime_type: String column

DATABASE LAYER (db.py)
├── insert_contacts(): Stores binary data
└── Queries return SQLAlchemy ORM objects with bytes in profile_image

API LAYER (api.py)
├── search_contacts(): Returns dict with profile_image as bytes
├── list_all_contacts(): Returns dict with profile_image as bytes
├── get_contact_details(): Returns dict with profile_image as bytes
├── get_contacts_by_tag(): Returns dict with profile_image as bytes
├── get_contacts_by_note(): Returns dict with profile_image as bytes
└── execute_sql(): Returns dict with ANY columns selected, including profile_image as bytes

LLM LAYER (llm_ollama.py)
├── _call_tool(): Receives result from API
├── Line 1339: Attempts json.dumps(tool_result) WITHOUT serializer
│   └── CRASHES when tool_result contains bytes (from profile_image)
├── Line 1359: json.dumps with serializer (PROTECTED)
│   └── Properly handles bytes using _json_serializer
└── _generate_directory(): CORRECTLY removes profile_image before JSON
    └── Uses the correct pattern for handling binary data

TOOL-SPECIFIC HANDLING
├── search_contacts/list_all_contacts: Return bytes, used by TUI (OK)
├── execute_sql: Returns bytes, passed to LLM (PROBLEM!)
├── _generate_directory: Returns bytes, explicitly removes them (CORRECT!)
└── All other tools: Return bytes as part of contact objects
```

## 11. KEY FILES AND LINE NUMBERS

| File | Lines | Purpose | Issue |
|------|-------|---------|-------|
| models.py | 28-78 | Contact schema with profile_image binary column | None - correct schema |
| db.py | 322-334 | Insert contacts with profile images | None - correct storage |
| api.py | 191-196 | execute_sql result handling | CRITICAL: Returns binary data |
| api.py | 294-317 | search_contacts returns profile_image | OK for TUI, not for JSON |
| llm_ollama.py | 1339 | Log execute_sql results | CRITICAL: Missing serializer |
| llm_ollama.py | 1354-1363 | Store tool results in history | OK: Has serializer |
| llm_ollama.py | 1486-1501 | _json_serializer method | Works correctly when used |
| llm_ollama.py | 840-862 | _generate_directory handling | CORRECT pattern to follow |

