# Phase 3 Design Decisions
## TUI Implementation for Issues #68-71

Generated: 2025-08-31
Purpose: Memorialize design decisions for Phase 3 Textual implementation

## UI Design Decisions

### 1. Contact View Layout (Issue #68)
- **No A-Z index column** - commands shown at bottom are sufficient
- **Three-pane layout**: Contact List | Preview
- **Navigation**: 
  - `j/k` or arrows for up/down
  - `A-Z` keys to jump to letter
  - `s` to switch to search
  - `Space` to select/toggle
  - `a` to add new contact

### 2. Relationship Creation (Issue #69)
- **Split-pane selector** for dual contact selection
- Contact 1 defaults to "You"
- Both panes searchable with fuzzy matching
- Relationship type selector below
- Visual confirmation before creation

### 3. Search & Export (Issue #70)
- **Immediate export**: `e` key exports selected items
- **Selection pattern**: `Space` toggles selection
- **Export formats**: CSV primary, keybindings for format selection
- Search results show in table with preview pane

### 4. Backup/Restore UI (Issue #71)
- **Backup slots** concept:
  - Top slot: "[enter a name for a new backup]" (grayed)
  - Below: Recent backups in reverse chronological order
  - Scrollable list
- **Restore behavior**:
  - Creates auto-backup before restore: "auto-backup-DATETIME"
  - Informs user they can restore auto-backup if needed
  - Non-destructive restore

### 5. "You" Contact
- **Auto-create on first run**
- Prompt for name (optional - can skip)
- If skipped: creates contact with first name "You"
- No other contact info required (user knows their own info)

### 6. Export Implementation
- Simple keybinding approach (no complex dialog needed)
- `c` for CSV, `v` for VCard, `j` for JSON
- Export happens immediately after format selection

### 7. Navigation & Modes
- **jkl navigation** in normal mode
- **Tab** freed for auto-completion
- **Auto-advance** to next field after selection
- **Mode switching**:
  - `ESC` to toggle between modes
  - Alternative: `Enter` to edit (in edit boxes), `ESC` to navigate
- Modes should work seamlessly, not feel modal

### 8. Status Bar
- **Show current mode prominently** (if using modes)
- **Selected item count** when items are selected
- **Context-sensitive help hints**
- Location/breadcrumb navigation

### 9. Testing Strategy
- **Business logic integration tests** - verify Phase 2 components work with UI
- **State management tests** - ensure selection persists across pagination
- **Keyboard navigation tests** - verify keybindings work
- **Skip visual/rendering tests** - will get these in user testing

### 10. Home Screen
- Simple menu with main actions:
  - `[c]` Contacts
  - `[r]` Relationships  
  - `[s]` Search
  - `[d]` Database
  - `[m]` Contact Metadata (tags/notes)
  - `[t]` Chat Mode
  - `[?]` Help
  - `[q]` Quit

## TUI Style Guide Adherence

Following PRT Text UI Style Guide principles:
- **Keyboard First**: All actions via keystrokes
- **Search → Select → Act** workflow pattern
- **Multi-pane navigation** where useful
- **Single-key actions** for common operations
- **Persistent status bar** with mode/selection info
- **No dead ends**: ESC or q always available
- **Immediate feedback** after actions

## Technical Architecture

### Widget Hierarchy
```
App
├── HomeScreen
├── ContactsScreen
│   ├── ContactTable (paginated)
│   └── ContactPreview
├── RelationshipsScreen
│   ├── DualContactSelector
│   └── RelationshipTypeSelector
├── SearchScreen
│   ├── SearchInput
│   ├── ResultsTable
│   └── ExportOptions
└── DatabaseScreen
    └── BackupSlots
```

### State Management
- SelectionSystem (Phase 2) handles multi-select
- PaginationSystem (Phase 2) handles large lists
- AutocompleteEngine (Phase 2) powers search inputs
- ValidationSystem (Phase 2) validates all inputs

### Integration Points
- All screens use Phase 2 components
- Business logic remains in core layer
- Textual only handles presentation/interaction
- State persists across screen changes

## Implementation Order

1. Base application structure & navigation
2. Home screen with menu
3. Contact view with pagination
4. Search with autocomplete
5. Relationship creation with dual selector
6. Database backup/restore
7. Export functionality
8. Polish & keybinding refinement

## Notes for Implementation

- Start with TDD: write failing tests for business logic integration
- Keep widgets thin - logic in Phase 2 components
- Ensure keyboard navigation works before adding features
- Test with 5000+ contacts early to catch performance issues
- Follow established error handling patterns from Phase 1