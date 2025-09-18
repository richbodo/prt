# 🚀 Automated Textual Development & Debugging Workflow

A comprehensive automated workflow for testing and debugging Textual applications with focus on layout issues, containers, scrolling, and screen resizing.

## 🎯 Overview

This workflow provides:
- **Automated console setup** with `textual console` integration
- **Comprehensive logging** with `self.log()` and structured debug output
- **Visual debugging** with `self.app.notify()` and CSS debug helpers
- **Screenpipe integration** for visual analysis and automated screenshots
- **Layout profiling** and responsive behavior testing
- **Automated test scenarios** for common layout issues

## 🛠️ Components

### 1. Core Workflow (`textual_debug_workflow.py`)
The main orchestrator that manages all debugging services:
- Starts/stops Textual console automatically
- Manages web serve for browser inspection
- Integrates with screenpipe for visual debugging
- Provides automated test scenario execution
- Creates debug utilities and CSS helpers

### 2. Demo Application (`textual_debug_demo.py`)
A complete demo showing the workflow in action:
- Interactive debugging with keybindings
- Layout analysis and issue detection
- Responsive behavior testing
- Notification system integration
- Comprehensive logging examples

## 🚀 Quick Start

### Step 1: Setup Environment
```bash
cd /Users/richardbodo/src/prt
source prt_env/bin/activate
```

### Step 2: Start Debug Console
```bash
# Terminal 1 - Start the debug console
textual console --port 7342 -v
```

### Step 3: Run Your App with Debugging
```bash
# Terminal 2 - Run your app with full debugging
textual run --dev --port 7342 your_app.py

# Or run the demo
textual run --dev --port 7342 textual_debug_demo.py
```

### Step 4: Use Interactive Debugging
In the running app, use these keybindings:
- `d` - Toggle debug mode (visual borders)
- `l` - Log comprehensive layout analysis
- `n` - Test notification system
- `s` - Trigger screenshot capture
- `r` - Test responsive behavior
- `q` - Quit application

## 🔧 Advanced Usage

### Automated Workflow
```python
from textual_debug_workflow import run_debug_workflow

# Run complete automated debugging workflow
await run_debug_workflow("my_app.py", 
                         console_port=7342,
                         enable_screenpipe=True,
                         auto_screenshot=True,
                         verbose_logging=True)
```

### Custom Test Scenarios
```python
async def my_layout_test():
    """Custom test scenario for specific layout issues"""
    log("🧪 Testing custom layout behavior")
    
    # Your test logic here
    await asyncio.sleep(1)
    
    log("✅ Custom test completed")

# Add to workflow
test_scenarios = [my_layout_test]
await workflow.run_app_with_debugging("my_app.py", test_scenarios)
```

## 📊 Debug Features

### 1. Layout Analysis
- **Widget tree inspection** with size and style information
- **Overflow detection** for widgets exceeding screen bounds
- **Responsive behavior testing** at multiple screen sizes
- **Container hierarchy analysis** with layout type identification

### 2. Visual Debugging
- **Debug CSS classes** for temporary borders and highlights
- **Container type visualization** (Horizontal=cyan, Vertical=magenta, Grid=orange)
- **Scrollable region highlighting** with green borders
- **Overflow issue marking** with yellow backgrounds

### 3. Performance Monitoring
- **Render time tracking** for layout performance issues
- **Widget count monitoring** for complexity analysis
- **Memory usage tracking** for resource optimization
- **Scroll performance analysis** for smooth scrolling validation

### 4. Automated Testing
- **Layout regression testing** with visual comparison
- **Responsive behavior validation** across screen sizes
- **Interaction testing** with simulated user input
- **Error condition testing** for edge cases

## 🖥️ Screenpipe Integration

The workflow integrates with screenpipe for advanced visual debugging:

### Features
- **Automatic screenshots** at key debugging points
- **Visual diff analysis** for layout changes
- **Terminal content search** for specific UI states
- **Interaction recording** for test scenario replay

### Usage
```python
# Enable screenpipe integration
session = DebugSession(
    app_path="my_app.py",
    enable_screenpipe=True,
    auto_screenshot=True
)

# Capture specific states
await workflow.capture_layout_state("after_resize")
await workflow.take_screenshot("button_clicked")
```

## 📋 Debug CSS Classes

Add these classes to your widgets for visual debugging:

```css
/* Temporary debugging borders */
.debug-border { border: solid red; }
.debug-container { border: solid blue; background: rgba(0, 0, 255, 0.1); }
.debug-scrollable { border: solid green; background: rgba(0, 255, 0, 0.1); }
.debug-overflow { border: solid yellow; background: rgba(255, 255, 0, 0.2); }

/* Layout type highlighting */
Horizontal { border: solid cyan; }
Vertical { border: solid magenta; }
Grid { border: solid orange; }
```

## 🔍 Common Debug Patterns

### Layout Issues
```python
def debug_layout_issues(app):
    """Check for common layout problems"""
    issues = []
    
    for widget in app.query("*"):
        # Check for zero/negative sizes
        if widget.size.width <= 0 or widget.size.height <= 0:
            issues.append(f"Invalid size: {widget.__class__.__name__}")
            
        # Check for overflow
        if widget.size.width > app.screen.size.width:
            issues.append(f"Width overflow: {widget.__class__.__name__}")
            
        # Check for missing scrollbars
        if (hasattr(widget, 'children') and 
            len(list(widget.walk_children())) > 10 and
            widget.styles.overflow_y != "auto"):
            issues.append(f"May need scrolling: {widget.__class__.__name__}")
    
    return issues
```

### Responsive Testing
```python
def test_responsive_behavior(app, test_sizes=None):
    """Test app at different screen sizes"""
    if test_sizes is None:
        test_sizes = [(80, 24), (120, 30), (160, 40), (200, 50)]
    
    for width, height in test_sizes:
        log(f"🔍 Testing at {width}x{height}")
        
        # Check widget behavior at this size
        for widget in app.query("*"):
            if widget.size.width > width:
                log(f"⚠️  {widget.__class__.__name__} exceeds width")
            if widget.size.height > height:
                log(f"⚠️  {widget.__class__.__name__} exceeds height")
```

### Performance Profiling
```python
import time

def profile_layout_performance(app):
    """Profile layout rendering performance"""
    start_time = time.time()
    
    # Trigger layout recalculation
    app.screen.refresh()
    
    render_time = time.time() - start_time
    
    metrics = {
        "render_time": render_time,
        "widget_count": len(list(app.screen.walk_children())),
        "screen_size": app.screen.size,
        "performance_score": 1.0 / render_time if render_time > 0 else float('inf')
    }
    
    log(f"📊 Performance metrics: {metrics}")
    return metrics
```

## 🎮 Interactive Debug Commands

When running with the debug workflow, you have access to these commands:

### Console Commands
- `log("message")` - Log to debug console
- `log(widget_tree=app.screen.tree)` - Log widget hierarchy
- `log(metrics=get_layout_metrics())` - Log performance metrics

### App Methods
- `self.log("debug info")` - Widget/App logging
- `self.notify("message", severity="info")` - User notifications
- `self.action_screenshot()` - Trigger screenshot
- `self.debug_layout()` - Comprehensive layout analysis

### CSS Debug Classes
- Add `.debug-border` for temporary borders
- Add `.debug-container` for container highlighting
- Add `.debug-scrollable` for scroll region marking

## 🔧 Configuration Options

### DebugSession Configuration
```python
session = DebugSession(
    app_path="my_app.py",
    console_port=7342,          # Textual console port
    serve_port=8000,            # Web serve port
    enable_screenpipe=True,     # Enable visual debugging
    auto_screenshot=True,       # Automatic screenshots
    layout_profiling=True,      # Performance monitoring
    verbose_logging=True        # Detailed log output
)
```

### Environment Variables
```bash
export TEXTUAL_DEBUG=1          # Enable debug mode
export TEXTUAL_LOG_LEVEL=DEBUG  # Verbose logging
export SCREENPIPE_ENABLED=1     # Enable screenpipe integration
```

## 🚨 Troubleshooting

### Common Issues

1. **Console not connecting**
   ```bash
   # Check if port is in use
   lsof -i :7342
   
   # Use different port
   textual console --port 7343
   ```

2. **App not showing debug output**
   ```bash
   # Ensure --dev flag is used
   textual run --dev --port 7342 my_app.py
   
   # Check console is running first
   textual console --port 7342
   ```

3. **Screenpipe integration failing**
   ```bash
   # Check screenpipe is installed and running
   which screenpipe
   screenpipe --version
   ```

4. **Layout issues not detected**
   ```python
   # Add explicit debug CSS classes
   widget.add_class("debug-border")
   
   # Use manual layout logging
   self.log(widget_tree=self.screen.tree)
   ```

## 📚 Best Practices

### 1. Development Workflow
1. Always start with `textual console` in a separate terminal
2. Use `--dev` flag for live CSS editing
3. Add debug CSS classes temporarily for visual inspection
4. Use structured logging with context information
5. Capture screenshots at key debugging points

### 2. Layout Debugging
1. Start with widget tree analysis (`self.log(self.tree)`)
2. Check container hierarchy and layout types
3. Verify overflow settings for scrollable content
4. Test responsive behavior at multiple screen sizes
5. Profile performance for complex layouts

### 3. Testing Strategy
1. Create automated test scenarios for common issues
2. Use visual regression testing with screenshots
3. Test edge cases (very small/large screens)
4. Validate accessibility and keyboard navigation
5. Monitor performance metrics over time

## 🎯 Next Steps

This workflow provides a solid foundation for Textual debugging. Consider these enhancements:

1. **Enhanced Screenpipe Integration** - Deeper integration with screenpipe MCP server
2. **Automated Visual Testing** - Screenshot comparison and diff analysis
3. **Performance Benchmarking** - Automated performance regression detection
4. **Layout Validation Rules** - Custom rules for layout correctness
5. **Integration Testing** - Multi-app testing scenarios

The workflow is designed to be extensible - you can add custom debug functions, test scenarios, and analysis tools as needed for your specific use cases.
