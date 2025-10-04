# 🎯 Issue #114 Implementation Plan: TUI Top Nav Dropdown

## 📋 Issue Summary
**Title**: TUI top nav  
**Number**: #114  
**Status**: OPEN  
**Goal**: Replace current top nav with Alt-triggered dropdown menu in upper left corner

## 🎯 Requirements Analysis

### **Current State**
- Uses standard Textual `Header()` widget (line 188 in `app.py`)
- **Current top nav**: ⭘ symbol visible in upper left corner of header
- Navigation currently via home screen menu (`NavigationMenu` widget)
- ⭘ symbol is the existing top nav dropdown that needs to be replaced

### **Target State** 
- **Closed state**: Shows "(Alt opens Menu)" in upper left corner
- **Open state**: Shows "(Alt closes Menu)" with dropdown menu
- **Menu items**: (B)ack to previous screen, (H)ome screen, (?)Help screen
- **Trigger**: Alt key binding for toggle
- **Help screen**: New implementation with key bindings reference

## 🚀 Implementation Plan with TUI Debug Integration

### **Phase 1: Analysis & Setup** (Day 1)

#### **Task 1.1: Analyze Current Implementation** ✅ IN PROGRESS
```bash
# Use TUI debug workflow for analysis
# Terminal 1: Start debug console
textual console --port 7342 -v

# Terminal 2: Run app with debugging  
textual run --dev --port 7342 python -m prt_src

# Use debug keybindings:
# 'd' - Toggle debug borders to see current header layout
# 'l' - Log widget tree to understand header structure
```

**Findings**:
- Current header is standard Textual `Header()` widget
- No existing "O" menu found in codebase
- Navigation handled by `NavigationMenu` widget in home screen
- Header styling in `styles.tcss` lines 10-15

#### **Task 1.2: Design New Top Nav Widget**
Create `prt_src/tui/widgets/top_nav_dropdown.py`:

```python
class TopNavDropdown(ModeAwareWidget):
    """Alt-triggered dropdown menu in header."""
    
    is_open = reactive(False)
    
    def __init__(self):
        super().__init__()
        self.menu_items = [
            MenuItem("b", "Back", "Go to previous screen", "back"),
            MenuItem("h", "Home", "Go to home screen", "home"), 
            MenuItem("?", "Help", "Show help screen", "help"),
        ]
```

#### **Task 1.3: TDD Test Setup**
Create `tests/test_top_nav_dropdown.py`:
```python
async def test_alt_key_toggles_menu():
    """Test Alt key opens/closes menu"""
    
async def test_menu_items_navigation():
    """Test B/H/? keys work in dropdown"""
    
async def test_visual_state_indicators():
    """Test (Alt opens Menu) vs (Alt closes Menu) text"""
```

### **Phase 2: Core Implementation** (Day 2)

#### **Task 2.1: Create TopNavDropdown Widget**
**TUI Debug Strategy**: Use `d` key to visualize widget boundaries during development

```python
# Key features to implement:
# - Alt key binding for toggle
# - Dropdown positioning (upper left)
# - Menu item selection and activation
# - Visual state indicators
```

#### **Task 2.2: Integrate with App Header**
Modify `prt_src/tui/app.py`:
```python
def compose(self) -> ComposeResult:
    """Compose with new top nav."""
    # Replace standard Header() with custom header containing dropdown
    yield TopNavHeader()  # New custom header widget
    yield Container(...)
    yield Footer()
```

#### **Task 2.3: CSS Styling**
Add to `prt_src/tui/styles.tcss`:
```css
/* Top Nav Dropdown */
.top-nav-dropdown {
    dock: top;
    height: 1;
    width: 100%;
    background: $panel;
}

.top-nav-closed {
    content-align: left middle;
    padding: 0 1;
}

.top-nav-open {
    height: 5;  /* Expand for dropdown menu */
}

.dropdown-menu {
    background: $panel;
    border: round $border;
    padding: 1;
}
```

### **Phase 3: Help Screen Implementation** (Day 3)

#### **Task 3.1: Create Help Screen**
Create `prt_src/tui/screens/help.py`:

```python
class HelpScreen(BaseScreen):
    """Help screen with key bindings reference."""
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("🆘 PRT Help & Key Bindings", classes="help-title")
            
            # Key bindings reference from TUI docs
            yield Static("Navigation:", classes="help-section-title")
            yield Static("Alt - Toggle top nav menu", classes="help-item")
            yield Static("ESC - Back/Cancel/Mode toggle", classes="help-item")
            yield Static("? - Show this help", classes="help-item")
            
            # Screen-specific bindings
            yield Static("Home Screen:", classes="help-section-title")
            # ... (extract from TUI_Key_Bindings.md)
```

#### **Task 3.2: Register Help Screen**
Add to screen registry and navigation logic.

### **Phase 4: Integration & Testing** (Day 4)

#### **Task 4.1: Navigation Integration**
Integrate with existing `NavigationService`:
- Back functionality using nav stack
- Home navigation
- Help screen routing

#### **Task 4.2: TUI Debug Testing**
Use comprehensive debug workflow:

```bash
# Debug session for testing
textual console --port 7342 -v  # Terminal 1
textual run --dev --port 7342 python -m prt_src  # Terminal 2

# Test scenarios with debug keybindings:
# 1. Press Alt - verify menu opens (use 'd' to see borders)
# 2. Press B/H/? - verify navigation works (use 'l' for layout analysis)
# 3. Test across different screens (use 'r' for responsive testing)
# 4. Screenshot capture for visual regression (use 's' key)
```

#### **Task 4.3: Cross-Screen Testing**
Test dropdown behavior on all screens:
- Home, Contacts, Search, Chat, etc.
- Verify Alt key doesn't conflict with existing bindings
- Ensure dropdown positioning works on all screen layouts

### **Phase 5: Cleanup & Documentation** (Day 5)

#### **Task 5.1: Remove Legacy Code**
- Search for any unused "O" menu code
- Remove associated tests if they exist
- Clean up unused imports

#### **Task 5.2: Update Documentation**
Update TUI documentation:
- `docs/TUI/TUI_Specification.md` - Add top nav dropdown specification
- `docs/TUI/TUI_Key_Bindings.md` - Add Alt key binding
- `docs/TUI/TUI_Style_Guide.md` - Update navigation patterns

## 🔧 Technical Implementation Details

### **Alt Key Binding Strategy**
```python
# App-level binding for Alt key
BINDINGS = [
    Binding("alt", "toggle_top_nav", "Toggle Top Nav", priority=True),
    # ... existing bindings
]

async def action_toggle_top_nav(self) -> None:
    """Toggle the top nav dropdown menu."""
    if hasattr(self.screen, 'top_nav'):
        await self.screen.top_nav.toggle()
```

### **Dropdown Widget Architecture**
```python
class TopNavDropdown(ModeAwareWidget):
    """Alt-triggered dropdown in header."""
    
    is_open = reactive(False)
    
    def compose(self) -> ComposeResult:
        if self.is_open:
            yield Static("(Alt closes Menu)", classes="nav-indicator")
            with Vertical(classes="dropdown-menu"):
                for item in self.menu_items:
                    yield Static(item.display_text, classes="dropdown-item")
        else:
            yield Static("(Alt opens Menu)", classes="nav-indicator")
    
    async def toggle(self) -> None:
        """Toggle dropdown open/closed state."""
        self.is_open = not self.is_open
        await self.recompose()  # Rebuild layout based on state
```

### **Menu Item Handling**
```python
def handle_menu_selection(self, key: str) -> None:
    """Handle menu item selection."""
    if key == "b":
        # Back to previous screen via NavigationService
        self.app.nav_service.pop()
    elif key == "h": 
        # Home screen
        await self.app.switch_screen("home")
    elif key == "?":
        # Help screen
        await self.app.switch_screen("help")
```

## 🧪 TUI Debug Integration Strategy

### **Development Workflow**
1. **Start each development session** with 2-terminal debug setup
2. **Use debug keybindings** throughout implementation:
   - `d` - Visualize widget boundaries and layout structure
   - `l` - Log widget tree to understand hierarchy
   - `n` - Test notifications for user feedback
   - `s` - Capture screenshots for visual regression testing
   - `r` - Test responsive behavior at different screen sizes

### **Specific Debug Applications**

#### **Layout Development**
```bash
# When implementing dropdown positioning:
# 1. Press 'd' to see container boundaries
# 2. Press 'l' to log widget tree and verify hierarchy
# 3. Press 's' to capture visual state for comparison
```

#### **Key Binding Testing**
```bash
# When testing Alt key functionality:
# 1. Use debug console to see key event logs
# 2. Verify Alt key doesn't conflict with existing bindings
# 3. Test across different screens for consistency
```

#### **Performance Testing**
```bash
# When optimizing dropdown performance:
# 1. Press 'r' to test responsive behavior
# 2. Monitor console for render time metrics
# 3. Test with debug borders to see layout recalculation
```

## 📊 Success Criteria

### **Functional Requirements**
- ✅ Alt key toggles dropdown menu
- ✅ Closed state shows "(Alt opens Menu)"
- ✅ Open state shows "(Alt closes Menu)" with menu items
- ✅ (B)ack navigates to previous screen
- ✅ (H)ome navigates to home screen  
- ✅ (?)Help shows new help screen with key bindings

### **Technical Requirements**
- ✅ No conflicts with existing key bindings
- ✅ Works consistently across all screens
- ✅ Proper integration with NavigationService
- ✅ Responsive layout that works at different screen sizes
- ✅ Clean removal of any legacy "O" menu code

### **Quality Requirements**
- ✅ Comprehensive test coverage with TDD approach
- ✅ Consistent with existing TUI style guide
- ✅ Performance validated with debug workflow
- ✅ Documentation updated to reflect new navigation

## 🎮 Testing Strategy with Debug Workflow

### **Manual Testing Checklist**
```bash
# 1. Basic functionality
textual run --dev --port 7342 python -m prt_src
# - Press Alt, verify menu opens
# - Press Alt again, verify menu closes
# - Test B/H/? keys in open state

# 2. Cross-screen testing  
# - Navigate to different screens
# - Test Alt key on each screen
# - Verify consistent behavior

# 3. Layout testing
# - Press 'd' to see debug borders
# - Press 'l' to analyze widget tree
# - Press 'r' to test responsive behavior

# 4. Performance testing
# - Monitor console for render times
# - Test rapid Alt key toggling
# - Verify no memory leaks or widget proliferation
```

### **Automated Testing**
```python
# Use Textual's testing framework with debug integration
async def test_top_nav_with_debug():
    async with app.run_test() as pilot:
        # Test Alt key functionality
        await pilot.press("alt")
        
        # Use debug workflow to verify state
        # (integrate debug analysis into test assertions)
```

## 📁 Files to Create/Modify

### **New Files**
- `prt_src/tui/widgets/top_nav_dropdown.py` - Main dropdown widget
- `prt_src/tui/screens/help.py` - Help screen implementation
- `tests/test_top_nav_dropdown.py` - TDD tests for dropdown
- `tests/test_help_screen.py` - Tests for help screen

### **Modified Files**
- `prt_src/tui/app.py` - Replace Header() with custom header
- `prt_src/tui/styles.tcss` - Add dropdown CSS styles
- `prt_src/tui/widgets/__init__.py` - Export new widgets
- `docs/TUI/TUI_Specification.md` - Update with top nav spec
- `docs/TUI/TUI_Key_Bindings.md` - Add Alt key binding

## 🎉 Expected Outcomes

### **User Experience**
- **Consistent navigation** available from any screen via Alt key
- **Clear visual indicators** for menu state
- **Quick access** to common navigation actions (Back/Home/Help)
- **Discoverable help system** with comprehensive key binding reference

### **Developer Experience**  
- **TUI debug workflow integration** throughout development
- **Comprehensive test coverage** with visual validation
- **Clean, maintainable code** following established patterns
- **Updated documentation** reflecting new navigation paradigm

### **Technical Benefits**
- **Reduced navigation complexity** - common actions in one place
- **Consistent key bindings** across all screens
- **Improved accessibility** with clear help system
- **Performance validated** through debug workflow monitoring

This plan leverages the comprehensive TUI debugging system we created to ensure high-quality implementation with real-time visual feedback, automated issue detection, and systematic testing throughout the development process.
