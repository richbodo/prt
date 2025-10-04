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

*This document should be updated as we discover more TUI development patterns and solutions.*
