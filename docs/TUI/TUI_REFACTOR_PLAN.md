# TUI Refactoring Plan - Issue #120

## Executive Summary

This plan outlines a complete refactoring of the PRT TUI to address critical issues with usability, testability, and container proliferation. We will rebuild the TUI to match the simplified [TUI_Specification.md](TUI_Specification.md) and [TUI_Style_Guide.md](TUI_Style_Guide.md), focusing on a clean, minimal implementation that prioritizes simplicity and debuggability.

## Current State Analysis

### What's Wrong
1. **Container Proliferation**: Multiple containers with random UUIDs causing visual artifacts (multiple borders at bottom of screen)
2. **Unusable**: Complex nested structures make the TUI difficult to navigate and use
3. **Untestable**: Current design makes it hard to write meaningful tests
4. **Over-engineered**: Too many containers, widgets, and abstractions getting in the way

### What's Working (Keep These)
1. **Services Layer**:
   - `prt_src/tui/services/data.py` - DataService for database operations
   - `prt_src/tui/services/navigation.py` - NavigationService for screen management
   - `prt_src/tui/services/notification.py` - NotificationService for user feedback
   - `prt_src/tui/services/llm_status.py` - LLM status monitoring

2. **Reusable Widgets** (evaluate each):
   - `prt_src/tui/widgets/base.py` - ModeAwareWidget base class (may need simplification)
   - `prt_src/tui/widgets/progress_indicator.py` - Progress display (if simple)
   - `prt_src/tui/widgets/navigation_menu.py` - May need simplification to match new spec

3. **App Infrastructure**:
   - `prt_src/tui/app.py` - Main app with mode management and first-run detection
   - `prt_src/tui/types.py` - Type definitions
   - Mode system (Nav/Edit modes)
   - First-run handler

### What to Delete
1. **All Screen Implementations**: Blow away everything in `prt_src/tui/screens/`
2. **All Screen Tests**: Remove all screen-specific tests
3. **Complex Widgets**: Delete widgets that don't match the new simple spec:
   - `contact_detail.py`, `contact_list.py`, `search_filter.py`, `relationship.py`, `settings.py`
4. **CSS File**: Delete `prt_src/tui/styles.tcss` - start fresh with minimal CSS

## New Architecture Principles

### 1. Simplicity First
- **No extra containers** unless absolutely necessary
- **Flat widget hierarchy** - avoid deep nesting
- **Single responsibility** - each screen does one thing well
- **Minimal CSS** - only what's needed for layout and theme

### 2. Testability
- **Pure functions** for business logic separate from UI
- **Mockable services** - all external dependencies injected
- **Predictable state** - clear state machines for screens
- **Integration tests** - test real user workflows

### 3. Debuggability
- **Clear widget names/IDs** - no random UUIDs for permanent widgets
- **Comprehensive logging** - log all state changes
- **Visual debugging** - use Textual devtools effectively
- **Error recovery** - graceful degradation, not crashes

## Screen Implementation Order

Rebuild screens one at a time, with tests and documentation for each.

### Phase 1: Core Navigation (Screens 1-2)

#### Screen 1: Home Screen
**Priority**: CRITICAL - Entry point for entire app

**Layout** (per spec):
```
┌─ Top Nav ────────────────────────────────┐
│ (N)av menu closed  │  HOME  │  Mode: Nav │
├──────────────────────────────────────────┤
│                                           │
│ * Chat - opens chat screen                │
│ * Search - opens search screen            │
│ * Settings - opens settings screen        │
│                                           │
│                                           │
│                                           │
│                                           │
├─ Bottom Nav ─────────────────────────────┤
│ (esc) Toggle Nav/Edit (x) Exit (?) Help  │
└──────────────────────────────────────────┘
```

**Components**:
- Top Nav bar (single line) with dropdown menu button, screen name, mode indicator
- Three text options (not a complex menu widget, just text)
- Bottom status bar (single line)
- Dropdown menu overlay (N key toggles)

**Key Bindings**:
- `N` - Toggle nav menu dropdown
- `C` - Open Chat (when menu open or in nav mode)
- `S` - Open Search (when menu open or in nav mode)
- `T` - Open Settings (when menu open or in nav mode)
- `ESC` - Toggle mode
- `X` - Exit app
- `?` - Help

**Tests**:
- Test home screen renders
- Test menu toggle
- Test navigation to each screen
- Test mode switching
- Test keyboard shortcuts

**Deliverables**:
- `prt_src/tui/screens/home.py` - New simple implementation
- `tests/test_home_screen.py` - Comprehensive tests
- Updated `docs/TUI/SCREENS/HOME.md` - Screen documentation

#### Screen 2: Help Screen
**Priority**: HIGH - Needed for user guidance

**Layout**:
```
┌─ Top Nav ────────────────────────────────┐
│ (N)av menu closed  │  HELP  │  Mode: Nav │
├──────────────────────────────────────────┤
│                                           │
│ Help not implemented yet.                 │
│                                           │
├─ Bottom Nav ─────────────────────────────┤
│ (esc) Toggle Nav/Edit (x) Exit (?) Help  │
└──────────────────────────────────────────┘
```

**Components**:
- Top Nav bar
- Single line of text
- Bottom status bar

**Deliverables**:
- `prt_src/tui/screens/help.py`
- `tests/test_help_screen.py`
- `docs/TUI/SCREENS/HELP.md`

### Phase 2: Core Functionality (Screens 3-5)

#### Screen 3: Chat Screen
**Priority**: HIGH - Core user interaction feature

**Layout** (per spec):
```
┌─ Top Nav ────────────────────────────────┐
│ (N)av menu closed  │  CHAT  │  Mode: Nav │
├─ Chat Status ────────────────────────────┤
│ ✅ LLM: Online │ READY                    │
├─ Chat Box ───────────────────────────────┤
│ Enter your prompt here...                 │
│ (Multi-line, scrollable)                  │
│                                           │
├─ Response Box ───────────────────────────┤
│ LLM responses appear here                 │
│ (Scrollable, last 64KB)                   │
│                                           │
│                                           │
├─ Bottom Nav ─────────────────────────────┤
│ (esc) Toggle Nav/Edit (x) Exit (?) Help  │
└──────────────────────────────────────────┘
```

**Components**:
- Chat Status Line (LLM status + progress indicator)
- Chat Box (TextArea widget, few lines high, scrollable)
- Response Box (RichLog or Static, scrollable, 64KB limit)

**Key Bindings**:
- `Enter` - Send message (in edit mode)
- `Shift+Enter` - New line in chat box
- `ESC` - Toggle mode / back to home
- `N` - Open nav menu

**Integration**:
- Use existing `llm_status.py` service
- Use existing Ollama integration from `prt_src/llm_ollama.py`
- Async message handling

**Tests**:
- Test chat box input
- Test message sending
- Test response display
- Test LLM status updates
- Test 64KB buffer limit
- Mock Ollama responses

**Deliverables**:
- `prt_src/tui/screens/chat.py`
- `tests/test_chat_screen.py`
- `docs/TUI/SCREENS/CHAT.md`

#### Screen 4: Search Screen
**Priority**: HIGH - Core data access feature

**Layout** (per spec):
```
┌─ Top Nav ────────────────────────────────┐
│ (N)av menu closed  │ SEARCH │  Mode: Nav │
├─ Search Edit Box ────────────────────────┤
│ Enter search text...                      │
│ (3 lines, editable)                       │
│                                           │
├─ Search Type Buttons ────────────────────┤
│ (1) Contacts  (2) Relationships           │
│ (3) Relationship_Types  (4) Notes         │
│ (5) Tags                                  │
├─ Search Results ─────────────────────────┤
│ Results appear here...                    │
│ (Scrollable, no pagination yet)           │
│                                           │
├─ Bottom Nav ─────────────────────────────┤
│ (esc) Toggle Nav/Edit (x) Exit (?) Help  │
└──────────────────────────────────────────┘
```

**Components**:
- Search Edit Box (TextArea, 3 lines)
- Five buttons for search type selection
- Results display (Static or RichLog, scrollable)

**Key Bindings**:
- `1-5` - Select search type (in nav mode)
- `Enter` - Execute search (in edit mode)
- `ESC` - Toggle mode
- Mouse clicks on buttons

**Search Logic**:
- Simple string matching for now
- No pagination (all results displayed)
- No filtering yet
- Future: "Search-Select-Act" loop

**Tests**:
- Test search input
- Test search type selection
- Test search execution for each data type
- Test results display
- Test empty results
- Test large result sets

**Deliverables**:
- `prt_src/tui/screens/search.py`
- `tests/test_search_screen.py`
- `docs/TUI/SCREENS/SEARCH.md`

#### Screen 5: Settings Screen
**Priority**: MEDIUM - Configuration and status

**Layout** (per spec):
```
┌─ Top Nav ────────────────────────────────┐
│ (N)av menu closed  │SETTINGS│  Mode: Nav │
├─ Database Status ────────────────────────┤
│ 🟢 Connected │ Contacts: 45 │ Tags: 12   │
│ Relationships: 23 │ Notes: 8              │
├──────────────────────────────────────────┤
│                                           │
│ (Future: Import/Export options)           │
│                                           │
│                                           │
├─ Bottom Nav ─────────────────────────────┤
│ (esc) Toggle Nav/Edit (x) Exit (?) Help  │
└──────────────────────────────────────────┘
```

**Components**:
- Database Status Line (connection status + row counts)
- Placeholder for future features

**Integration**:
- Query database for counts
- Connection status monitoring

**Tests**:
- Test status display
- Test database connection monitoring
- Test count accuracy

**Deliverables**:
- `prt_src/tui/screens/settings.py`
- `tests/test_settings_screen.py`
- `docs/TUI/SCREENS/SETTINGS.md`

### Phase 3: Future Enhancements (Not in Spec Yet)

These screens exist in the old TUI but are NOT in the new spec. We'll evaluate if/when to add them back:

- Wizard Screen (first-run setup)
- Contact Detail Screen
- Contact Form Screen
- Relationships Screen
- Relationship Types Screen
- Relationship Form Screen
- Metadata Screen
- Import/Export Screens
- Database Screen

## Shared Components Refactoring

### Top Nav Component
Create a reusable TopNav widget:

```python
class TopNav(Static):
    """Top navigation bar with menu, screen name, and mode indicator."""

    def __init__(self, screen_name: str, **kwargs):
        self.screen_name = screen_name
        self.menu_open = False

    def compose(self) -> ComposeResult:
        # Single line: menu button | screen name | mode
        yield Static(self._format_nav_line())

    def toggle_menu(self):
        self.menu_open = not self.menu_open
        self.update(self._format_nav_line())
```

### Bottom Nav Component
Create a reusable BottomNav widget:

```python
class BottomNav(Static):
    """Bottom status bar with key hints and status messages."""

    def __init__(self, **kwargs):
        self.status_message = ""

    def compose(self) -> ComposeResult:
        # Single line: key hints | status message
        yield Static(self._format_status_line())

    def show_status(self, message: str):
        self.status_message = message
        self.update(self._format_status_line())
```

### Dropdown Menu Component
Create a simple dropdown overlay:

```python
class DropdownMenu(Static):
    """Simple dropdown menu overlay."""

    def __init__(self, items: list[tuple[str, str]], **kwargs):
        # items = [(key, label), ...]
        self.items = items

    def compose(self) -> ComposeResult:
        # Vertical list of menu items
        for key, label in self.items:
            yield Static(f"({key.upper()}) {label}")
```

## CSS Strategy

### Minimal CSS Approach
Start with bare minimum CSS for layout:

```css
/* Top Nav - single line, always visible */
TopNav {
    height: 1;
    dock: top;
    background: $panel;
}

/* Bottom Nav - single line, always visible */
BottomNav {
    height: 1;
    dock: bottom;
    background: $panel;
}

/* Dropdown Menu - overlay when visible */
DropdownMenu {
    display: none;  /* Toggle with display: block */
    layer: overlay;
    offset: 0 1;  /* Below top nav */
    width: 40;
    background: $surface;
    border: solid $primary;
}

/* Screen-specific minimal styles */
ChatBox {
    height: 5;
    border: solid $primary;
}

ResponseBox {
    border: solid $primary;
}

SearchEditBox {
    height: 3;
    border: solid $primary;
}
```

### CSS Testing Strategy
- Test CSS in isolation with visual debug mode
- Use explicit colors during development
- Switch to theme variables for production
- Document any CSS quirks in TUI_Dev_Tips.md

## Testing Strategy

### Unit Tests (per screen)
- Render tests (screen appears correctly)
- Key binding tests (each key does what it should)
- State transition tests (mode switching, navigation)
- Service interaction tests (mocked)

### Integration Tests (after Phase 2)
- Full navigation flow (home → chat → search → settings → home)
- Cross-screen workflows
- Service integration (real database, mocked LLM)
- Error handling

### Manual Testing Checklist
For each screen:
- [ ] Screen renders without visual artifacts
- [ ] Top nav displays correctly
- [ ] Bottom nav displays correctly
- [ ] All key bindings work
- [ ] Mode switching works
- [ ] Navigation to/from other screens works
- [ ] Screen-specific functionality works
- [ ] Error states display properly

## Migration Strategy

### Step 1: Preparation (Before Coding)
1. **Backup Current TUI**:
   ```bash
   git checkout -b backup-old-tui
   git push origin backup-old-tui
   git checkout main
   ```

2. **Create Refactor Branch**:
   ```bash
   git checkout -b refactor-tui-issue-120
   ```

3. **Document Current Widget Inventory**:
   - List all widgets and their dependencies
   - Identify which to keep, simplify, or delete
   - Save as `docs/TUI/WIDGET_INVENTORY.md`

### Step 2: Deletion (Clean Slate)
1. Delete all screen files except `base.py`
2. Delete screen tests
3. Delete `styles.tcss`
4. Create stub `styles.tcss` with minimal base styles
5. Update `__init__.py` to remove deleted screens
6. Commit: "Remove old TUI screens and tests for refactor"

### Step 3: Rebuild (One Screen at a Time)
For each screen in Phase 1, then Phase 2:
1. Create new screen implementation
2. Create comprehensive tests
3. Create screen documentation
4. Manual test with Textual devtools
5. Commit with descriptive message
6. Iterate if issues found

### Step 4: Widget Evaluation (During Rebuild)
As we build screens, evaluate each existing widget:
- Does it match the new spec?
- Is it simple enough?
- Can we simplify it?
- Should we delete it and rebuild?

Document decisions in `docs/TUI/WIDGET_DECISIONS.md`

### Step 5: Integration (After All Screens)
1. Write integration tests for full workflows
2. Performance testing with large datasets
3. Memory leak testing (run for extended period)
4. Update main documentation

## Development Workflow (Per Screen)

### 1. Read Spec
- Review TUI_Specification.md for screen details
- Review TUI_Style_Guide.md for design principles
- Review TUI_Dev_Tips.md for known issues

### 2. Design Screen
- Sketch layout (ASCII art in doc)
- List components needed
- Identify reusable widgets
- Plan key bindings

### 3. Write Tests (TDD)
- Write failing tests for screen behavior
- Start with simple render test
- Add tests for each feature

### 4. Implement Screen
- Create minimal working version
- Use Textual devtools for visual debugging
- Iterate until tests pass

### 5. Document Screen
- Create detailed screen documentation
- Include screenshots if possible
- Document known issues

### 6. Review and Iterate
- Manual testing with checklist
- Fix bugs found
- Refactor for simplicity
- Update tests

## Documentation Structure

Create organized documentation:

```
docs/TUI/
├── TUI_Specification.md          # Overall spec (existing)
├── TUI_Style_Guide.md            # Design principles (existing)
├── TUI_Dev_Tips.md               # Development tips (existing)
├── TUI_Key_Bindings.md           # Key bindings (existing, update)
├── TUI_REFACTOR_PLAN.md          # This document
├── WIDGET_INVENTORY.md           # Widget evaluation (create)
├── WIDGET_DECISIONS.md           # Widget keep/delete decisions (create)
├── IMPORT_EXPORT_SCREENS.md      # Old doc (keep for reference)
└── SCREENS/                      # Screen-specific docs (create)
    ├── HOME.md
    ├── HELP.md
    ├── CHAT.md
    ├── SEARCH.md
    └── SETTINGS.md
```

## Success Criteria

We'll know the refactor is successful when:

### Functionality
- [ ] All 5 screens in spec are implemented and working
- [ ] Navigation flows correctly between screens
- [ ] Mode switching works consistently
- [ ] Key bindings work as documented
- [ ] Services integrate properly
- [ ] No visual artifacts (container proliferation solved)

### Code Quality
- [ ] No unnecessary containers
- [ ] Flat widget hierarchy (max 2-3 levels)
- [ ] Clear, readable code
- [ ] Comprehensive tests (>80% coverage)
- [ ] All tests passing
- [ ] No memory leaks

### Documentation
- [ ] Each screen has detailed documentation
- [ ] Key bindings documented
- [ ] Development tips updated
- [ ] Migration notes for future developers

### User Experience
- [ ] TUI is usable and responsive
- [ ] No confusing visual elements
- [ ] Clear feedback for actions
- [ ] Keyboard-first navigation works smoothly
- [ ] Error messages are clear

## Risk Management

### Known Risks

1. **Risk**: Breaking existing functionality users depend on
   - **Mitigation**: Keep old code in backup branch, document migration

2. **Risk**: Textual framework limitations/quirks
   - **Mitigation**: Test frequently with devtools, document workarounds

3. **Risk**: Service layer may need changes
   - **Mitigation**: Evaluate services early, make minimal changes

4. **Risk**: Scope creep (adding features not in spec)
   - **Mitigation**: Strict adherence to spec, create future features list

### Rollback Plan

If refactor fails or takes too long:
1. Create detailed status document
2. Merge what's working
3. Flag remaining work in issues
4. Consider alternative approaches

## Timeline Estimate

This is a rough estimate, assuming focused work:

- **Phase 1** (Home + Help): 2-3 days
  - Home screen: 1.5 days
  - Help screen: 0.5 days
  - Integration: 0.5 days

- **Phase 2** (Chat + Search + Settings): 5-7 days
  - Chat screen: 2-3 days (LLM integration complexity)
  - Search screen: 2-3 days (multiple search types)
  - Settings screen: 1 day
  - Integration: 1 day

- **Testing & Documentation**: 2-3 days
  - Integration tests: 1 day
  - Documentation: 1 day
  - Bug fixes: 1 day

**Total**: 9-13 days of focused development

## Next Steps

1. **Review this plan** with stakeholders
2. **Create widget inventory** document
3. **Set up refactor branch** and backup
4. **Start Phase 1** with Home screen
5. **Iterate** based on learnings

## Questions for Review

Before starting implementation:

1. Is the screen priority order correct?
2. Are there any "must-have" screens not in the spec?
3. Should we keep wizard screen for first-run?
4. What's the minimum viable first release?
5. Any concerns about the deletion strategy?

---

**Document Status**: Draft for Review
**Created**: 2025-10-08
**Author**: Claude Code (Issue #120)
**Next Review**: After stakeholder feedback
