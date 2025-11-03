# LLM Tool Chaining Examples

This document provides examples of how to chain tools together using the memory system for complex workflows.

## Memory System Overview

The memory system allows you to:
1. Save query results with `save_contacts_with_images`
2. List saved results with `list_memory`
3. Use saved results with other tools like `generate_directory`

## Example Workflows

### Creating Directory from Contacts with Images

**User Request**: "Create a directory of all contacts with images"

**Chaining Pattern**:
```
Step 1: save_contacts_with_images
  -> Returns: memory_id (e.g., "contacts_143052_a1b2c3d4")

Step 2: generate_directory
  -> Parameters: memory_id="contacts_143052_a1b2c3d4"
  -> Creates: Interactive directory with images
```

**Sample Interaction**:
```
LLM: I'll first get all contacts with images and save them for directory creation.

Tool Call: save_contacts_with_images
  description: "contacts with images for directory"

Result:
{
  "success": true,
  "memory_id": "contacts_143052_a1b2c3d4",
  "count": 25,
  "message": "Saved 25 contacts with images to memory"
}

LLM: Now I'll create the directory using those saved contacts.

Tool Call: generate_directory
  memory_id: "contacts_143052_a1b2c3d4"
  output_name: "contacts_with_images"

Result: Directory created with 25 contacts at /path/to/directory
```

### Working with Multiple Query Results

**User Request**: "Show me what's in memory, then create a directory from the most recent contacts"

**Chaining Pattern**:
```
Step 1: list_memory
  -> Shows available memory IDs and descriptions

Step 2: generate_directory
  -> Uses memory_id from the list
```

## Key Principles

1. **Save First, Use Later**: Always save query results before using them with other tools
2. **Descriptive IDs**: Memory IDs are human-readable (e.g., "contacts_143052_a1b2c3d4")
3. **Automatic Cleanup**: Memory expires after 24 hours to prevent clutter
4. **Flexible Chaining**: Any tool can work with saved results, not just specific combinations

## Memory Management

- `save_contacts_with_images()` - Save optimized contacts query
- `list_memory()` - See what's available
- Memory auto-expires after 24 hours
- Results include metadata: count, description, creation time

## Performance Benefits

- **Query Once, Use Many**: Expensive contact queries run once, reused multiple times
- **Fast Chaining**: Directory generation uses pre-loaded data
- **Memory Efficient**: Binary image data handled separately from JSON