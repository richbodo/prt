# JSON Command Schema for LLM Database Bridge

This document defines the JSON command format that the LLM must produce in response to user queries.

## Design Principles

1. **Consistent Structure**: All commands have the same top-level fields
2. **Type Safety**: Clear parameter types for validation
3. **Extensibility**: Easy to add new intent types
4. **LLM-Friendly**: Simple enough for LLM to generate reliably
5. **Validation-Ready**: Required fields are explicit

---

## Base Command Structure

All commands follow this structure:

```json
{
  "intent": "<intent_type>",
  "parameters": { /* intent-specific parameters */ },
  "confidence": 0.95,  // Optional: LLM's confidence in parsing (0-1)
  "reasoning": "..."   // Optional: Why this intent was chosen
}
```

**Required Fields**:
- `intent` (string): The type of action to perform
- `parameters` (object): Intent-specific parameters

**Optional Fields**:
- `confidence` (float 0-1): LLM's confidence in the parse
- `reasoning` (string): Brief explanation (useful for debugging)

---

## Intent Types

### 1. Search Intent

**Purpose**: Initial database query or new search (replaces current results)

**Intent**: `"search"`

**Parameters**:
```json
{
  "entity_type": "contacts",  // "contacts", "relationships", "notes"
  "filters": {
    "tags": ["tech", "python"],           // Optional: filter by tags
    "location": "San Francisco",          // Optional: location match
    "name_contains": "john",              // Optional: name substring
    "date_range": {                       // Optional: date filtering
      "start": "2024-01-01",              // ISO date or "YYYY-MM-DD"
      "end": "2024-12-31"
    },
    "has_email": true,                    // Optional: must have email
    "has_phone": true,                    // Optional: must have phone
    "custom_field": {                     // Optional: custom field match
      "field": "company",
      "value": "Google"
    }
  },
  "limit": 50,                            // Optional: max results (default 50)
  "sort_by": "name"                       // Optional: "name", "date_added", "last_contact"
}
```

**Examples**:

*"Show me all my contacts"*
```json
{
  "intent": "search",
  "parameters": {
    "entity_type": "contacts"
  }
}
```

*"Find tech people in SF"*
```json
{
  "intent": "search",
  "parameters": {
    "entity_type": "contacts",
    "filters": {
      "tags": ["tech"],
      "location": "San Francisco"
    }
  }
}
```

*"Contacts I met in 2024"*
```json
{
  "intent": "search",
  "parameters": {
    "entity_type": "contacts",
    "filters": {
      "date_range": {
        "start": "2024-01-01",
        "end": "2024-12-31"
      }
    }
  }
}
```

---

### 2. Refine Intent

**Purpose**: Modify existing search results (add or remove filters)

**Intent**: `"refine"`

**Parameters**:
```json
{
  "operation": "add_filter",  // "add_filter" or "remove_filter"
  "filter_type": "location",  // "tags", "location", "name_contains", "date_range", etc.
  "filter_value": "Oakland"   // The value to add/remove
}
```

**Examples**:

*"Just the ones in Oakland"* (after showing SF results)
```json
{
  "intent": "refine",
  "parameters": {
    "operation": "add_filter",
    "filter_type": "location",
    "filter_value": "Oakland"
  }
}
```

*"Ignore location"*
```json
{
  "intent": "refine",
  "parameters": {
    "operation": "remove_filter",
    "filter_type": "location"
  }
}
```

*"Only colleagues"*
```json
{
  "intent": "refine",
  "parameters": {
    "operation": "add_filter",
    "filter_type": "tags",
    "filter_value": "colleague"
  }
}
```

---

### 3. Select Intent

**Purpose**: Choose items from current results for further action

**Intent**: `"select"`

**Parameters**:
```json
{
  "selection_type": "ids",  // "ids", "range", "all", "none", "filter"
  "selection_value": [1, 2, 5],  // Type depends on selection_type
  "replace": true           // Optional: replace selection (default) or add to it
}
```

**Selection Types**:

| Type | Value Type | Description | Example |
|------|-----------|-------------|---------|
| `ids` | array of ints | Specific indices | `[1, 2, 5]` |
| `range` | `{start: int, end: int}` | Range of indices | `{start: 1, end: 10}` |
| `all` | null | Select all current results | `null` |
| `none` | null | Clear selection | `null` |
| `filter` | filter object | Content-based selection | `{location: "SF"}` |

**Examples**:

*"Select 1, 2, 3"*
```json
{
  "intent": "select",
  "parameters": {
    "selection_type": "ids",
    "selection_value": [1, 2, 3]
  }
}
```

*"Select the first 5"*
```json
{
  "intent": "select",
  "parameters": {
    "selection_type": "range",
    "selection_value": {"start": 1, "end": 5}
  }
}
```

*"Select all"*
```json
{
  "intent": "select",
  "parameters": {
    "selection_type": "all",
    "selection_value": null
  }
}
```

*"Select everyone in SF from that list"* (content-based)
```json
{
  "intent": "select",
  "parameters": {
    "selection_type": "filter",
    "selection_value": {
      "location": "San Francisco"
    }
  }
}
```

---

### 4. Export Intent

**Purpose**: Export selected or all items to a file

**Intent**: `"export"`

**Parameters**:
```json
{
  "format": "json",           // "json", "directory", "csv"
  "scope": "selected",        // "selected" or "all"
  "destination": "/path/to/file.json",  // Optional: file path
  "include_images": true,     // Optional: include profile images (for directory)
  "include_relationships": true,  // Optional: include relationship data
  "include_notes": true       // Optional: include notes
}
```

**Export Formats**:
- `json` - Full JSON export with all data
- `directory` - Format for `make_directory.py` tool (HTML directory)
- `csv` - Flattened CSV export

**Examples**:

*"Export to json"*
```json
{
  "intent": "export",
  "parameters": {
    "format": "json",
    "scope": "all"
  }
}
```

*"Export selected for directory maker"*
```json
{
  "intent": "export",
  "parameters": {
    "format": "directory",
    "scope": "selected",
    "include_images": true
  }
}
```

*"Save as csv to /tmp/contacts.csv"*
```json
{
  "intent": "export",
  "parameters": {
    "format": "csv",
    "scope": "all",
    "destination": "/tmp/contacts.csv"
  }
}
```

---

### 5. View Details Intent

**Purpose**: Show full details of specific item(s)

**Intent**: `"view_details"`

**Parameters**:
```json
{
  "item_ids": [1, 3],         // Indices from current results
  "include_relationships": true,  // Optional: show relationships
  "include_notes": true,      // Optional: show notes
  "include_history": true     // Optional: show contact history
}
```

**Examples**:

*"Show me details for #3"*
```json
{
  "intent": "view_details",
  "parameters": {
    "item_ids": [3],
    "include_relationships": true,
    "include_notes": true
  }
}
```

*"Show full details for 1, 2, and 5"*
```json
{
  "intent": "view_details",
  "parameters": {
    "item_ids": [1, 2, 5],
    "include_relationships": true,
    "include_notes": true,
    "include_history": true
  }
}
```

---

### 6. Error Response

**Purpose**: LLM couldn't parse the intent

**Intent**: `"error"`

**Parameters**:
```json
{
  "error_type": "ambiguous",  // "ambiguous", "unsupported", "missing_info"
  "message": "I need more information...",
  "suggestions": [
    "Try: 'show me tech contacts'",
    "Try: 'find people in SF'"
  ]
}
```

**Error Types**:
- `ambiguous` - Query has multiple interpretations
- `unsupported` - Requested action not supported
- `missing_info` - Need more details to proceed

**Example**:

*"Find them"* (no context)
```json
{
  "intent": "error",
  "parameters": {
    "error_type": "missing_info",
    "message": "I need more details. Who would you like to find?",
    "suggestions": [
      "Try: 'find tech contacts'",
      "Try: 'show me everyone in SF'"
    ]
  }
}
```

---

## Validation Rules

### Required Field Validation

Each intent type MUST include:
1. `intent` field (string, non-empty)
2. `parameters` field (object, can be empty `{}`)

### Intent-Specific Validation

**search**:
- MUST have `entity_type` ("contacts", "relationships", "notes")
- Filters are optional but if present must be valid filter types

**refine**:
- MUST have `operation` ("add_filter" or "remove_filter")
- MUST have `filter_type` (valid filter name)
- `filter_value` required for "add_filter", optional for "remove_filter"

**select**:
- MUST have `selection_type` ("ids", "range", "all", "none", "filter")
- `selection_value` type must match selection_type

**export**:
- MUST have `format` ("json", "directory", "csv")
- MUST have `scope` ("selected" or "all")

**view_details**:
- MUST have `item_ids` (array of integers, non-empty)

**error**:
- MUST have `error_type` (valid error type)
- MUST have `message` (non-empty string)

### Type Validation

- **String fields**: Non-empty unless explicitly optional
- **Integer arrays**: All elements must be positive integers
- **Date strings**: Must be ISO format "YYYY-MM-DD" or parseable
- **Boolean fields**: Must be `true` or `false` (not truthy/falsy)
- **Confidence**: If present, must be float between 0 and 1

---

## Edge Cases and Special Handling

### Empty Results

If a search returns no results, the LLM should still produce a valid search command. The application handles empty results, not the LLM.

### Ambiguous Queries

If the query is ambiguous, the LLM should return an `error` intent with `error_type: "ambiguous"` and suggestions.

### Unsupported Operations

If the user asks for something not supported (e.g., "delete all contacts"), the LLM should return an `error` intent with `error_type: "unsupported"`.

### Selection Without Prior Search

If the user says "select 1, 2, 3" without any search results displayed, the LLM should return an `error` intent with `error_type: "missing_info"`.

### Content-Based Selection Limitations

Content-based selection (e.g., "select everyone in SF") should only be used when the filter is simple and unambiguous. Complex filters should prompt for clarification.

---

## Anti-Patterns (What NOT to Do)

### ❌ Don't Hallucinate Data

```json
{
  "intent": "search",
  "parameters": {
    "entity_type": "contacts",
    "filters": {
      "tags": ["john_smith"]  // ❌ Don't make up tags that weren't mentioned
    }
  }
}
```

### ❌ Don't Invent Fields

```json
{
  "intent": "export",
  "parameters": {
    "format": "pdf",  // ❌ Only json, directory, csv are supported
    "fancy_styling": true  // ❌ No such field exists
  }
}
```

### ❌ Don't Assume Context

```json
{
  "intent": "select",
  "parameters": {
    "selection_type": "ids",
    "selection_value": [1, 2, 3],
    "from_previous_search": "tech contacts"  // ❌ Don't add extra context
  }
}
```

### ❌ Don't Over-Engineer

```json
{
  "intent": "search",
  "parameters": {
    "entity_type": "contacts",
    "filters": {
      "tags": ["tech"],
      "location": "San Francisco"
    },
    "metadata": {  // ❌ Unnecessary nesting
      "user_query": "find tech people in SF",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  }
}
```

---

## Summary

This schema provides:
- ✅ **6 intent types** (search, refine, select, export, view_details, error)
- ✅ **Consistent structure** (intent + parameters)
- ✅ **Clear validation rules** (required fields, type checking)
- ✅ **LLM-friendly** (simple, consistent patterns)
- ✅ **Extensible** (easy to add new intent types later)

Next steps:
1. Write system prompt that teaches the LLM this schema
2. Create promptfoo tests to validate LLM can produce these commands
3. Implement parser/validator in Phase 2
