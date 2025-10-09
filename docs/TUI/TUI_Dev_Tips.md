# TUI Development Tips for PRT Textual Application

This document captures important lessons learned during TUI development with the Textual framework.

## Widget Inheritance Patterns

### ✅ **Correct Widget Base Classes**
All custom widgets in PRT should inherit from proven base classes:

```python
# For text content widgets
class MyWidget(Static):
    def compose(self) -> ComposeResult:
        self.update("My content here")
        return super().compose()

# For mode-aware widgets  
class MyModeWidget(ModeAwareWidget):  # Inherits from Static
    pass
```

### ❌ **Avoid Base Widget Class for Content**
```python
# DON'T DO THIS - causes text rendering issues
class MyWidget(Widget):
    def compose(self) -> ComposeResult:
        yield Label("Content")  # Won't render properly
```

**Lesson**: The base `Widget` class doesn't handle text content rendering like `Static` does.

## Text Content Display

### ✅ **Use Static.update() for Text Content**
```python
class ProgressIndicator(Static):
    def show_message(self, text: str):
        self.update(text)  # Direct content update - reliable
```

### ❌ **Avoid Complex Child Widget Structures**
```python
# DON'T DO THIS - causes layout conflicts
def compose(self) -> ComposeResult:
    with Horizontal():
        yield Label("Spinner")
        yield Label("Message")
```

**Lesson**: Simple direct content is more reliable than nested Label widgets.

## CSS Layout Issues

### **Height Consistency**
Ensure container and content heights match:
```css
.my-widget {
    height: 3;  /* Container height */
}

.my-widget-content {
    height: 3;  /* Content must match container */
}
```

### **Border Gaps Issue**
When borders have gaps or render inconsistently:

**Problem**: Using `border: thick white` or conflicting CSS rules
```css
/* DON'T DO THIS - causes gaps */
.widget {
    border: thick white;  /* Hardcoded colors */
    height: 3;
}
.widget-content {
    height: 1;  /* Height mismatch */
}
```

**Solution**: Use theme variables and consistent heights
```css
/* DO THIS - clean borders */
.widget {
    border-top: solid $primary;
    border-bottom: solid $primary;
    height: 1;
    padding: 0;
    margin: 0;
}
```

### **Color Inheritance**
Use explicit colors instead of theme variables for debugging:
```css
/* Debugging - use explicit colors */
.debug-widget {
    background: red;
    color: white;
}

/* Production - use theme variables */
.widget {
    background: $panel;
    color: $text;
}
```

## Widget Lifecycle

### **Content Updates**
- Use `self.update()` for Static widgets
- Use `label.update()` for Label widgets after mounting
- Check widget mounting state before complex operations

### **UI Refresh Timing - CRITICAL**
**Problem**: Textual batches UI updates until async operations complete
```python
# WRONG - UI won't update until entire method finishes
async def process_data():
    widget.display = True
    await long_running_operation()
    widget.display = False
```

**Solution**: Force UI refresh with delays
```python
# CORRECT - UI updates immediately
async def process_data():
    widget.display = True
    self.refresh()  # Force immediate UI update
    await asyncio.sleep(0.1)  # Allow UI to render
    
    await long_running_operation()
    
    widget.display = False
    self.refresh()  # Force immediate hide
```

**Key Points**:
- Call `self.refresh()` after display state changes
- Add small delays (`await asyncio.sleep(0.1)`) to allow rendering
- Without refresh calls, all UI updates appear simultaneously at the end

### **Timer Management**
```python
# Reliable timer pattern
if hasattr(self, 'set_interval') and callable(self.set_interval):
    self._timer = self.set_interval(0.1, self._update_method)
else:
    # Fallback for unmounted widgets
    pass
```

## Debugging Strategies

### **Visual Debugging**
1. **Make it obvious**: Use bright colors, large text, emojis
2. **Test inheritance**: Try `Static` vs `Widget` base classes
3. **Simplify structure**: Remove nested containers when debugging
4. **Check mounting**: Ensure widgets are fully composed before content updates

### **Common Issues**
- **Red box, no text**: Wrong base class (use `Static`)
- **Border gaps**: Height mismatches in CSS
- **Invisible content**: Theme variable resolution issues
- **Layout conflicts**: Complex nested structures

### **Logging-Based Debugging**

**CRITICAL**: TUIs are event-driven and hide state behind rendering. Always add comprehensive logging FIRST when debugging.

#### Standard Logging Setup
```python
from prt_src.logging_config import get_logger
logger = get_logger(__name__)
```

Logs automatically go to `prt_data/prt.log` (INFO level by default).

#### Essential Logging Patterns

**Event Handlers - Log entry, state, decisions:**
```python
def on_key(self, event) -> None:
    key = event.key.lower()
    logger.info(f"[SCREEN] on_key: key='{key}', dropdown={self.dropdown.display}")

    if key == "n":
        logger.info("[SCREEN] Handling 'n' - toggling menu")
        self.action_toggle_menu()
        event.prevent_default()
```

**Navigation - Log screen stack (critical for catching double-push bugs):**
```python
def navigate_to(self, screen_name: str) -> None:
    logger.info(f"[APP] navigate_to('{screen_name}') STARTED")
    logger.info(f"[APP] Stack before: {[type(s).__name__ for s in self.screen_stack]}")

    self.push_screen(new_screen)

    logger.info(f"[APP] Stack after: {[type(s).__name__ for s in self.screen_stack]}")
```

**Actions - Log before/after state:**
```python
def action_go_back(self) -> None:
    logger.info("[SCREEN] action_go_back STARTED")
    logger.info(f"[SCREEN] Before: dropdown={self.dropdown.display}, menu={self.menu_open}")

    self.dropdown.hide()
    self.top_nav.menu_open = False

    logger.info(f"[SCREEN] After: dropdown={self.dropdown.display}, menu={self.menu_open}")
    self.app.pop_screen()
    logger.info("[SCREEN] action_go_back COMPLETED")
```

#### Viewing Logs During Development
```bash
# Terminal 1: Run TUI
python -m prt_src.tui

# Terminal 2: Watch logs in real-time
tail -f prt_data/prt.log

# Filter by component
tail -f prt_data/prt.log | grep '\[APP\]'

# Get recent event flow
tail -200 prt_data/prt.log | grep -E '\[HELP\]|\[APP\]|\[DROPDOWN\]'
```

#### Tag Convention
- `[APP]` - Application-level events
- `[SCREEN]` - Screen-specific events (use screen name like `[HOME]`, `[HELP]`)
- `[WIDGET]` - Widget events (use widget name like `[DROPDOWN]`, `[TOPNAV]`)
- `[SERVICE]` - Service events

#### Real Example: Double-Push Bug

**Problem**: "Pressing n,b on help screen requires two attempts to go back"

**Without logs**: Would require hours of code inspection and guesswork.

**With logs**: Immediately revealed the issue:
```
[APP] Stack before pop: ['Screen', 'HomeScreen', 'HelpScreen', 'HelpScreen']
```

The help screen was pushed **twice** due to duplicate event handlers. Screen stack logging caught it in seconds.

**Key Takeaway**: Log screen stack at every navigation point. Stack corruption is common and invisible without logging.

## Progress Indicator Specific

### **Working Pattern**
```python
class ChatProgressIndicator(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_animating = False
        
    def compose(self) -> ComposeResult:
        self.update("Initial content")
        return super().compose()
        
    async def start_animation(self):
        self._is_animating = True
        self.display = True
        self.update("🔄 Processing...")
        
        if hasattr(self, 'set_interval'):
            self._timer = self.set_interval(0.5, self._update_content)
            
    def _update_content(self):
        if self._is_animating:
            # Update content directly
            self.update("New content")
```

## Container Management Issues

### **Container Proliferation Problem**
**Symptom**: Multiple border artifacts appearing at bottom of screen
**Cause**: Creating new containers with random UUIDs instead of reusing main container

```python
# WRONG - Creates container accumulation
if not mount_successful:
    self.current_container_id = f"main-container-{uuid.uuid4().hex[:8]}"  # Random ID!
    await self.mount(Container(new_screen, id=self.current_container_id))
```

**Solution**: Use single fallback container
```python
# CORRECT - Reuses single fallback container
if not mount_successful:
    fallback_id = "fallback-container"
    # Remove existing fallback first
    try:
        existing = self.query_one(f"#{fallback_id}")
        await existing.remove()
    except:
        pass
    await self.mount(Container(new_screen, id=fallback_id))
```

### **Container Debugging**
Add container counting to identify leaks:
```python
# Debug container count
all_containers = self.query("Container") 
logger.info(f"Total containers: {len(all_containers)}")
```

### **Widget Positioning in Containers**
- Widgets mount in the **current active container**
- Progress indicators may mount in **wrong container** if container switching occurs
- Always verify widget is in the **intended container hierarchy**

## TUI Terminal Access

### **Critical Development Note**
**The TUI must be either exited or killed before the terminal it is running on can be accessed to run terminal commands.**

When the TUI is running in a terminal:
- **Terminal is blocked** - Cannot run additional commands in the same terminal
- **Must exit TUI first** - Press `q` to quit or `Ctrl+C` to force exit
- **Use separate terminals** - Debug console in Terminal 1, TUI in Terminal 2
- **Background processes** - Use `&` to run TUI in background if needed

### **Debug Workflow Terminal Management**
```bash
# Recommended 2-terminal setup:
# Terminal 1: Debug console (always available for commands)
textual console --port 7342 -v

# Terminal 2: TUI application (blocks terminal when running)
textual run --dev --port 7342 python -m prt_src

# To run commands while TUI is active:
# - Use Terminal 1 (debug console)
# - Or exit TUI first (press 'q'), run commands, restart TUI
```

## Best Practices

1. **Follow existing patterns** in the codebase
2. **Use Static for text content** widgets
3. **Keep widget structure simple** during development
4. **Test with obvious visual elements** first
5. **Check widget inheritance** when content doesn't render
6. **Use explicit CSS values** for debugging
7. **Verify widget mounting** before complex operations
8. **Avoid container proliferation** - reuse containers when possible
9. **Debug container count** when seeing multiple borders
10. **Always use 2-terminal setup** for TUI debugging to avoid blocking

## Framework-Specific Notes

### **Textual Widget Hierarchy**
- `Widget` - Base class, minimal functionality
- `Static` - Text content display, CSS styling support
- `ModeAwareWidget` - PRT custom class extending Static

### **Content Update Methods**
- `Static.update(text)` - Direct text content
- `Label.update(text)` - For Label widgets
- `RichLog.write(text)` - For log/chat displays

---

## Testing TUIs with Pilot

### The TUI Testing Paradigm Shift

**Critical Insight**: "The most effective way to test a terminal application is to not involve a terminal at all."

TUIs are hard to test with traditional tools because they:
- Transform the terminal into "application mode" (not line-based CLI)
- Use ANSI escape codes to paint a 2D canvas (not a queryable DOM)
- Bypass standard I/O streams (use raw device events)

**Textual's Solution**: Run tests in **headless mode** using the **Pilot** API.

### Why Pilot Works

```python
async with app.run_test() as pilot:
    # App runs WITHOUT a terminal
    # - No ANSI codes sent to screen
    # - Event loop runs in-memory
    # - Pilot injects events directly into asyncio queue
    # - Fast, deterministic, reliable
```

**Key Architecture**:
1. `App.run_test()` creates virtual display (no terminal needed)
2. Pilot injects Key/Click events into app's event queue
3. Events process exactly as in real terminal
4. Tests query widget state and assert outcomes

### Testing Methodology: Vibe-Coding vs Agent-Based

#### **Vibe-Coding** (Current - Human + Claude)

**Philosophy**: Test-After Development
```
Explore → Implement → Visual test → Write locking test
```

**Why**: Exploration needs freedom, tests lock in stable behavior

**What to test**:
- User journeys (not implementation details)
- Mode changes, navigation, input
- Visual snapshots for key screens

**When to write**:
- After feature stabilizes
- When fixing bugs (regression test)
- Before refactoring

#### **Agent-Based** (Future - Multi-Agent Team)

**Philosophy**: Test-Driven Development
```
Spec → Agent writes test → Agent implements → Test validates
```

**Why**: Agents can't see UI - tests are their only feedback

**What to test**:
- Everything (comprehensive coverage)
- Contract tests between agent-written modules
- Property-based tests for state machines

**When to write**:
- BEFORE any code (test = specification)
- For every feature and bug fix
- CI gates all merges

### The PRT Testing Pyramid

```
          /\
         /E2E\           ← 5% - Full user journeys
        /------\
       /Visual \         ← 15% - Snapshot tests
      /--------\
     /Integration\       ← 60% - Screen tests (MAJORITY)
    /------------\
   / Widget/Unit \       ← 20% - Component tests
  /----------------\
```

**Why this works for TUIs**: Pilot is SO fast that integration tests are nearly as cheap as unit tests.

### Test Organization

```
tests/
├── test_widgets/          # Widget unit tests
│   ├── test_dropdown_menu.py
│   └── test_chat_textarea.py
├── test_screens/          # Integration tests (MAJORITY)
│   ├── test_home_screen.py
│   ├── test_chat_screen.py
│   └── test_search_screen.py
├── test_snapshots/        # Visual regression tests
│   ├── test_home_snapshots.py
│   └── test_chat_snapshots.py
├── test_e2e/              # End-to-end workflows
│   └── test_navigation_flow.py
└── conftest.py            # Shared fixtures
```

### Standard Test Structure

```python
async def test_feature_name():
    """Clear description of what this test verifies."""
    # Arrange
    app = PRTApp()
    async with app.run_test() as pilot:
        # Act
        await pilot.press("c")  # Navigate to chat
        await pilot.pause()     # Wait for messages to process

        # Assert
        assert pilot.app.screen.screen_title == "CHAT"
```

### Essential Pilot Methods

#### Keyboard Input
```python
# Single key
await pilot.press("escape")

# Multiple keys (unpacking)
await pilot.press(*"hello")  # Types h,e,l,l,o

# Special keys
await pilot.press("enter", "tab", "up", "down")

# With modifiers
await pilot.press("ctrl+c")
```

#### Mouse Input
```python
# Click by selector
await pilot.click("#button-id")
await pilot.click(Button)

# Click with offset
await pilot.click(Button, offset=(10, 5))

# Click at screen coordinates
await pilot.click(offset=(20, 10))

# Double/triple click
await pilot.click("#widget", times=2)

# Click with modifiers
await pilot.click("#slider", control=True)
```

#### Timing & Synchronization
```python
# Wait for all pending messages
await pilot.pause()

# Wait with delay
await pilot.pause(delay=0.5)

# Wait for animation
await pilot.wait_for_animation()
```

#### Widget Queries
```python
# By ID
widget = pilot.app.query_one("#widget-id")

# By type
from textual.widgets import TextArea
input_widget = pilot.app.query_one(TextArea)

# Multiple matches
buttons = pilot.app.query(".action-button")

# With type hint
chat_input = pilot.app.query_one("#chat-input", TextArea)
```

### Common Test Patterns

#### Testing Mode Changes
```python
async def test_mode_toggle():
    app = PRTApp()
    async with app.run_test() as pilot:
        # Check initial mode
        assert pilot.app.current_mode == AppMode.NAVIGATION

        # Toggle mode
        await pilot.press("escape")
        await pilot.pause()

        # Verify mode changed
        assert pilot.app.current_mode == AppMode.EDIT
```

#### Testing Screen Navigation
```python
async def test_navigation():
    app = PRTApp()
    async with app.run_test() as pilot:
        # Navigate to screen
        await pilot.press("c")  # Chat screen
        await pilot.pause()

        # Verify navigation
        assert pilot.app.screen.screen_title == "CHAT"

        # Verify widgets mounted
        chat_input = pilot.app.query_one("#chat-input")
        assert chat_input is not None
```

#### Testing Input Focus
```python
async def test_input_focus():
    app = PRTApp()
    async with app.run_test() as pilot:
        await pilot.press("c")  # Navigate to chat
        await pilot.press("escape")  # Enter EDIT mode
        await pilot.pause()

        # Verify input has focus
        chat_input = pilot.app.query_one("#chat-input", TextArea)
        assert chat_input.has_focus
```

#### Testing Text Input
```python
async def test_typing():
    app = PRTApp()
    async with app.run_test() as pilot:
        await pilot.press("s")  # Search screen
        await pilot.press("escape")  # EDIT mode
        await pilot.pause()

        # Type text
        await pilot.press(*"test query")
        await pilot.pause()

        # Verify text entered
        search_input = pilot.app.query_one("#search-input", TextArea)
        assert search_input.text == "test query"
```

### Configuration & Running Tests

#### pytest.ini_options (pyproject.toml)
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # REQUIRED for Textual tests
testpaths = ["tests"]
```

#### Running Tests
```bash
# All tests
./prt_env/bin/python -m pytest tests/ -v

# Specific test file
./prt_env/bin/python -m pytest tests/test_pilot_demo.py -v

# Specific test
./prt_env/bin/python -m pytest tests/test_pilot_demo.py::test_mode_toggle -v

# With coverage
./prt_env/bin/python -m pytest tests/ --cov=prt_src --cov-report=html
```

### Debugging Test Failures

#### Common Issues

**1. Timing Issues**
```python
# ❌ BAD - Race condition
await pilot.press("enter")
assert some_state  # Might not be updated yet

# ✅ GOOD - Wait for processing
await pilot.press("enter")
await pilot.pause()  # Let messages process
assert some_state
```

**2. Widget Not Found**
```python
# ❌ BAD - Widget might not be mounted yet
await pilot.press("c")
widget = pilot.app.query_one("#widget")  # Might fail

# ✅ GOOD - Wait for screen to mount
await pilot.press("c")
await pilot.pause()
widget = pilot.app.query_one("#widget")
```

**3. Wrong Screen**
```python
# Always verify you're on the right screen
assert pilot.app.screen.screen_title == "CHAT"
# Then query widgets
```

### Snapshot Testing (Visual Regression)

```bash
# Install
pip install pytest-textual-snapshot
```

```python
def test_home_screen_appearance(snap_compare):
    """Snapshot test for home screen layout."""
    assert snap_compare("prt_src/tui/__main__.py")

def test_chat_with_input(snap_compare):
    """Snapshot of chat screen after typing."""
    async def setup(pilot):
        await pilot.press("c")  # Go to chat
        await pilot.press("escape")  # EDIT mode
        await pilot.press(*"Hello!")
        await pilot.pause()

    assert snap_compare(
        "prt_src/tui/__main__.py",
        run_before=setup
    )
```

```bash
# First run (generates baseline)
pytest tests/test_snapshots.py

# Update snapshots after UI change
pytest tests/test_snapshots.py --snapshot-update
```

### Testing Best Practices

1. **Write tests for user journeys**, not implementation details
2. **Always call `await pilot.pause()`** after actions that trigger async events
3. **Query widgets AFTER `pause()`** to ensure they're mounted
4. **Verify screen before querying** - assert you're on the right screen
5. **Use descriptive test names** - explain WHAT you're testing
6. **Keep tests focused** - one behavior per test
7. **Use fixtures** for common setup (in `conftest.py`)
8. **Test happy path AND error cases**
9. **Snapshot critical screens** - catch visual regressions
10. **Run tests before committing** - fast feedback loop

### When Tests Fail: Debugging Strategy

1. **Read the assertion error** - it shows actual vs expected
2. **Add print/log statements** - see what state actually is
3. **Run single test** - isolate the failure
4. **Check timing** - add more `pause()` calls
5. **Verify widget exists** - might not be mounted yet
6. **Check screen title** - might be on wrong screen
7. **Look at screen stack** - navigation might be broken
8. **Use `--tb=short`** - cleaner stack traces (already in pyproject.toml)

### Example: Greenfield Test

See `tests/test_pilot_demo.py` for a complete example demonstrating:
- Mode switching tests
- Navigation tests
- Input focus tests
- Placeholder text tests

Run it with:
```bash
./prt_env/bin/python -m pytest tests/test_pilot_demo.py -v
```

### Future: Testing for Agent-Based Development

When agents write code:
1. **Agent writes test from spec** (test = contract)
2. **Agent implements until test passes**
3. **CI runs ALL tests** before merge
4. **Visual snapshots catch UI breaks**
5. **Property-based tests** for complex state machines

**Why this matters**: Agents can't "see" the TUI running. Tests are their ONLY feedback mechanism.

---

*This document should be updated as we discover more TUI development patterns and solutions.*
