# Chat Screen Architecture

This document provides a high-level overview of the Chat screen's architecture as a conversational database interface.

## Vision

Transform the Chat screen into a **natural language wrapper around the Search-Select-Act workflow**, enabling users to query, filter, select, and act on data through conversation while maintaining all the power and safety of structured operations.

---

## Core Principles

1. **LLM as Translator, Not Renderer**
   - LLM parses intent → JSON commands
   - Code executes queries and formats results
   - No hallucinated data (LLM never makes up contacts/IDs)

2. **Context-Aware but Token-Efficient**
   - Minimal context by default (~500 tokens)
   - Expand to detailed only when needed (~2000 tokens)
   - Track conversation for continuity

3. **Configurable and Safe**
   - All LLM settings in JSON config
   - Permission system (create/update/delete controls)
   - Confirmation dialogs for risky operations
   - Audit logging for LLM-initiated changes

4. **Reusable Components**
   - Share formatters between Chat and Search screens
   - Common selection service (app-level)
   - Same workflow engine for both interfaces

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User (Natural Language)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      ChatScreen (TUI)                       │
│  • Handles user input (TextArea)                            │
│  • Displays formatted results (VerticalScroll)              │
│  • Manages modes (EDIT/NAV)                                 │
│  • Shows confirmation dialogs                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  LLMDatabaseBridge                          │
│  • Parses natural language → JSON commands                  │
│  • Validates command structure                              │
│  • Checks permissions                                       │
│  • Returns structured responses                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────┴────┐
                    ▼         ▼
      ┌─────────────────────────────┐    ┌───────────────────┐
      │   ChatContextManager        │    │ LLMConfigManager  │
      │  • Tracks conversation      │    │  • Load settings  │
      │  • Manages display state    │    │  • Permissions    │
      │  • Builds prompts           │    │  • System prompt  │
      │  • Resolves selections      │    └───────────────────┘
      └──────────────┬──────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              SearchSelectActWorkflow                        │
│  • Executes database queries                                │
│  • Manages selection state                                  │
│  • Dispatches actions (export, delete, edit)                │
│  • Tracks operation history                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
  ┌───────────────┐ ┌────────────┐ ┌──────────────┐
  │ResultsFormatter│ │SelectionSvc│ │ ExportService│
  │ • List format │ │ • Track IDs│ │ • JSON       │
  │ • Table format│ │ • Cross-ctx│ │ • Directory  │
  │ • Card format │ └────────────┘ │ • CSV        │
  │ • Tree format │                └──────────────┘
  └───────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│                       PRTAPI                                │
│  • Search contacts/relationships/notes                      │
│  • Create/update/delete operations                          │
│  • Data validation                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow: User Query → Result Display

### Example: "show me tech contacts in San Francisco"

```
1. USER TYPES MESSAGE
   ↓
2. ChatScreen.action_send_message()
   - Get message text
   - Pass to LLM bridge
   ↓
3. LLMDatabaseBridge.parse_user_intent()
   - Build prompt with context
   - Call LLM (via OllamaLLM)
   - Parse JSON response:
     {
       "intent": "search",
       "parameters": {
         "entity_type": "contacts",
         "filters": {
           "tags": ["tech"],
           "location": ["San Francisco"]
         }
       },
       "explanation": "Searching for tech contacts in SF"
     }
   ↓
4. SearchSelectActWorkflow.execute_search()
   - Call PRTAPI.search(entity_type='contacts', tags=['tech'], location=['SF'])
   - Returns list of Contact objects
   ↓
5. ResultsFormatter.render()
   - Format as numbered list:
     [1] Alice Chen (alice@example.com) - python, AI
     [2] Bob Martinez (bob@techcorp.com) - devops, cloud
     ...
   ↓
6. ChatContextManager.update_display()
   - Store results
   - Build index mapping: {1: contact_id_247, 2: contact_id_89, ...}
   - Cache for next query
   ↓
7. ChatScreen displays result
   - Show formatted results
   - Add hint: "Say 'select #' to choose items"
   - Auto-scroll to bottom
```

### Follow-up: "select 1 and 2"

```
1. USER TYPES "select 1 and 2"
   ↓
2. LLMDatabaseBridge.parse_user_intent()
   - Context includes: "Current display: 47 tech contacts in SF"
   - LLM returns:
     {
       "intent": "select",
       "parameters": {
         "selection_type": "ids",
         "ids": [1, 2]
       },
       "explanation": "Selected 2 contacts"
     }
   ↓
3. ChatContextManager.resolve_selection()
   - Map display indices [1, 2] → database IDs [247, 89]
   - Update selection state
   ↓
4. ChatScreen displays confirmation
   - "✓ Selected 2 items"
   - Show next actions: "Export, view details, or continue searching?"
```

---

## Key Components

### 1. LLMDatabaseBridge

**Responsibility**: Translate natural language → structured commands

**Key Methods**:
- `parse_user_intent(message, context)` → Command JSON
- `validate_command(command)` → Validates structure
- `get_system_prompt()` → Loads from config

**Configuration**:
- System prompt (customizable via config)
- Temperature, timeout, keep_alive
- Debug logging

### 2. ChatContextManager

**Responsibility**: Manage conversation state and context

**Key Methods**:
- `update_display(results, metadata)` → Store current display
- `build_prompt(message)` → Build context-aware prompt
- `resolve_selection(params)` → Map indices → database IDs
- `add_exchange(user, assistant)` → Track conversation

**State Tracked**:
- Current results (database objects)
- Display index mapping ({1: db_id, 2: db_id, ...})
- Conversation history (last N exchanges)
- Selection state (selected item IDs)

### 3. ResultsFormatter

**Responsibility**: Format database results for display

**Modes**:
- `numbered_list` - [1], [2], [3] with selection markers
- `table` - ASCII table with Rich
- `cards` - Detailed view with all fields
- `tree` - Hierarchical relationships
- `compact` - One-line summaries

**Reusable**: Same formatter used in Search screen

### 4. SearchSelectActWorkflow

**Responsibility**: Coordinate search → select → act operations

**Key Methods**:
- `execute_search(params)` → Query database
- `execute_selection(params)` → Update selection
- `execute_action(action, params)` → Export/delete/edit

**Reusable**: Same workflow for Chat and Search

### 5. LLMConfigManager

**Responsibility**: Load and validate LLM configuration

**Configuration Sections**:
- `llm` - Model, timeout, temperature
- `llm_permissions` - Safety controls
- `llm_prompts` - System prompt customization
- `llm_context` - Context management
- `llm_developer` - Debug tools

---

## Context Management Strategy

### The Challenge

LLMs have limited context windows. We need to provide enough context for accurate parsing without overwhelming the model.

### The Solution: Adaptive Context

**Three modes**:

1. **Minimal** (default, ~500 tokens)
   ```
   Current view: 47 tech contacts in San Francisco
   Display indices: [1] through [47]
   Currently selected: 2 items
   ```

2. **Detailed** (when needed, ~2000 tokens)
   ```
   [1] Alice Chen (SF) - tech, python, AI
   [2] Bob Martinez (Oakland) - devops, cloud
   ...
   ```

3. **Adaptive** (smart switching)
   - Use minimal for index-based queries ("select 1, 2, 3")
   - Use detailed for content queries ("select everyone in SF")

### Token Budget

With `max_context_tokens: 4000`:
- System prompt: ~500 tokens
- Conversation history (3 turns): ~600 tokens
- Current display: ~500-2000 tokens (adaptive)
- User message: ~50 tokens
- **Total**: ~1650-3150 tokens (well within budget)

---

## Permission System

### Configuration

```json
{
  "llm_permissions": {
    "allow_create": true,
    "allow_update": true,
    "allow_delete": false,
    "require_confirmation": {
      "create": false,
      "update": false,
      "delete": true,
      "bulk_operations": true
    },
    "max_bulk_operations": 100,
    "read_only_mode": false
  }
}
```

### Enforcement

```python
# Check permission before executing
if command['intent'] == 'delete':
    if not config.permissions.allow_delete:
        show_error("Delete operations are disabled")
        return

    if config.permissions.require_confirmation.delete:
        confirmed = await show_confirmation_dialog(
            "Delete 5 contacts?",
            ["Alice Chen", "Bob Martinez", ...],
            "Delete Forever"
        )
        if not confirmed:
            return

# Execute with audit logging
await workflow.execute_action('delete', ids=selected_ids)
log_llm_operation('delete', 'contacts', selected_ids, success=True)
```

---

## Testing Strategy

### Layered Approach

1. **Unit Tests** (< 1s)
   - Test deterministic components (formatters, context manager)
   - No LLM calls
   - 90%+ coverage

2. **Integration Tests** (< 5s)
   - Test workflows with mock LLM
   - Pre-defined responses
   - 80%+ coverage

3. **Contract Tests** (1-5m)
   - Test real LLM with promptfoo
   - Validate intent parsing accuracy (>95%)
   - Detect regressions

4. **E2E Tests** (5-10m, manual)
   - Test full system with real LLM
   - Run before releases
   - Validate critical user journeys

See [Chat_Screen_Testing_Strategy.md](./Chat_Screen_Testing_Strategy.md) for details.

---

## Implementation Phases

See [Chat_Screen_Implementation_Plan.md](./Chat_Screen_Implementation_Plan.md) for the complete phase-by-phase plan.

**Summary**:
- Phase 0: Infrastructure & config (12-18h)
- Phase 1: Deterministic components (16-21h)
- Phase 2: LLM bridge with mocks (16-21h)
- Phase 3: LLM contract testing (14-20h)
- Phase 4: Workflow implementation (19-24h)
- Phase 5: Real LLM integration (17-24h)
- Phase 6: Advanced features (14-19h)
- Phase 7: Regression suite (17-22h)

**Total**: 125-169 hours over 8-12 weeks

---

## Example Conversations

### Search → Refine → Select → Export

```
> show me all my contacts
Found 2,453 contacts. Let's narrow it down.

> people in tech
Found 687 contacts tagged 'tech'.

> San Francisco area
Refined to 234 contacts in SF, Oakland, Berkeley, Palo Alto.

> just colleagues
Found 89 colleagues in tech in the bay area:
[1] Alice Chen (SF) - Python, AI
[2] Bob Martinez (Oakland) - DevOps
...

> show me the ones I haven't talked to in 6 months
Narrowed to 23 contacts you haven't connected with recently:
[1] Alice Chen - last contact 8 months ago
[2] David Lee - last contact 7 months ago
...

> select the first 5
✓ Selected 5 contacts

> export them for the directory maker
✓ Exported to exports/directory_20250110_153022/

Run: python tools/make_directory.py generate exports/directory_20250110_153022/
```

### Content-Based Selection

```
> show me tech contacts
Found 47 tech contacts:
[1] Alice Chen (SF)
[2] Bob Martinez (Oakland)
...

> select everyone who works at Google
✓ Selected 3 contacts (Alice Chen, Carol White, David Park)

> export to json
✓ Exported to exports/contacts_20250110_154530.json
```

---

## Security & Safety

### Safeguards

1. **Permission Checks**
   - Validate before every write operation
   - Configurable per operation type
   - Read-only mode available

2. **Confirmation Dialogs**
   - Required for delete operations
   - Required for bulk operations (>10 items)
   - Show affected items

3. **Audit Logging**
   - Log all LLM-initiated operations
   - Include timestamp, operation, items, success/failure
   - Stored in `prt_data/audit.log`

4. **No Hallucinations**
   - LLM never formats results (code does)
   - LLM never makes up contact names/IDs
   - Validated with contract tests (0% hallucination rate)

### Future: Safe vs Dev Mode

**Dev Mode** (current):
- Full configuration control
- Custom system prompts
- All operations allowed

**Safe Mode** (future):
- Pre-approved prompt only
- Delete operations disabled by default
- Bulk operations require confirmation
- Suitable for end users

---

## Benefits of This Architecture

1. ✅ **Fast**: Most operations use minimal context (~500 tokens)
2. ✅ **Accurate**: 95%+ intent classification with contract testing
3. ✅ **Safe**: Permission system + confirmations + audit logs
4. ✅ **Testable**: 4-layer testing strategy with fast feedback
5. ✅ **Reusable**: Share components with Search screen
6. ✅ **Configurable**: All settings in JSON, developer-friendly
7. ✅ **Maintainable**: Clean separation of concerns
8. ✅ **Debuggable**: Extensive logging and debug modes

---

## Related Documentation

- **[LLM_Configuration.md](./LLM_Configuration.md)** - Complete configuration reference
- **[Chat_Screen_Implementation_Plan.md](./Chat_Screen_Implementation_Plan.md)** - Phase-by-phase implementation guide
- **[Chat_Screen_Testing_Strategy.md](./Chat_Screen_Testing_Strategy.md)** - Comprehensive testing approach
- **[TUI_Specification.md](./TUI_Specification.md)** - Overall TUI spec including Chat screen
- **[TUI_Style_Guide.md](./TUI_Style_Guide.md)** - Design principles and patterns
