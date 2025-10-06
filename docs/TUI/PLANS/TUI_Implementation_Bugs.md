# TUI Implementation Bugs - Progress Indicator Issues

## Current State

### What Works
- ✅ **Container mounting** - Yellow box appears in correct position
- ✅ **CSS styling** - Yellow background and red border render
- ✅ **Widget positioning** - Container appears between chat log and input
- ✅ **Timing logic** - Debug messages show correct start/stop timing
- ✅ **Container count reduction** - Fewer containers being created

### What Doesn't Work
- ❌ **Text content rendering** - No text visible in containers
- ❌ **Label.update() calls** - Content updates don't display
- ❌ **Static.update() calls** - Content updates don't display
- ❌ **Container proliferation** - Still creating extra containers on input

## Technical Details

### Environment
- **Framework**: Textual (Python TUI framework)
- **Platform**: macOS (Darwin 24.6.0)
- **Python**: 3.13.1
- **Terminal**: iTerm2/Terminal.app

### Code Structure
```
prt_src/tui/
├── app.py                 # Main app with container management
├── screens/chat.py        # Chat screen with progress indicator
├── widgets/progress_indicator.py  # Custom widget (not working)
├── styles.tcss           # CSS styling
└── services/llm_status.py # LLM status checking
```

### CSS Applied
```css
.chat-progress {
    height: 2;
    width: 100%;
    background: yellow;  /* Visible */
    color: black;        /* Should be visible */
    text-style: bold;
    border: thick solid red;  /* Visible */
    text-align: center;
    padding: 0;
    margin: 1;
}
```

## Hypotheses for Invisible Content

### Theory 1: Z-Index/Layer Issues
- Content might be rendered behind the background
- Text might be at wrong z-layer

### Theory 2: Font/Character Rendering
- Emojis might not render in this context
- Font issues causing invisible characters
- Terminal font compatibility problems

### Theory 3: Textual Framework Bug
- Bug in Textual's Label/Static content rendering
- Version compatibility issue
- Platform-specific rendering problem

### Theory 4: Layout Calculation Issues
- Text positioned outside visible area
- Overflow hidden cutting off content
- Alignment calculations failing

### Theory 5: Color Inheritance
- Text color being overridden by parent styles
- Theme variables causing color conflicts
- CSS cascade issues

## Observed Behavior Patterns

### Container Creation Timeline
1. **App starts** - Main container created
2. **Navigate to chat** - Chat screen mounted in main container
3. **Chat screen loads** - Yellow progress indicator container appears (empty)
4. **Submit query** - Extra container created at bottom of screen
5. **Processing completes** - All containers remain

### CSS Rendering Behavior
- **Background colors render correctly** (yellow, red)
- **Borders render correctly** (thick red borders)
- **Dimensions render correctly** (2 lines tall, full width)
- **Text content completely invisible** (all attempts)

## Debug Information Available

### Logging Output
```
🔥 PROGRESS DEBUG: Updated label directly
🔍 PRE-PROCESS: Total containers: X
🔍 POST-PROCESS: Total containers: Y
🔍 CONTAINER DEBUG: Total containers in app: Z
```

### Visual Evidence (via Screenpipe)
- Yellow containers appear in correct positions
- Red borders visible around containers
- No text content visible in any approach
- Multiple container borders at screen bottom
- Layout responsive to window width changes

## Next Investigation Steps

### Immediate Tests Needed
1. **Test with plain ASCII text** (no emojis) to rule out character issues
2. **Test with different colors** to rule out color inheritance
3. **Test minimal Label in other screens** to confirm Label functionality
4. **Check Textual version compatibility** and known issues

### Deep Investigation
1. **Examine Textual source code** for Label rendering issues
2. **Test on different terminal applications** to rule out terminal issues
3. **Create minimal reproduction case** outside PRT codebase
4. **Check for CSS cascade conflicts** in existing styles

### Alternative Approaches
1. **Use RichLog widget** for progress display (proven to work)
2. **Integrate progress into chat log** instead of separate widget
3. **Use notification system** for progress indication
4. **Implement in status bar** instead of separate container

## Files Modified During Investigation

### Core Files
- `prt_src/tui/app.py` - Container management fixes
- `prt_src/tui/screens/chat.py` - Progress indicator integration
- `prt_src/tui/styles.tcss` - CSS styling attempts

### New Files Created
- `prt_src/tui/services/llm_status.py` - LLM status checking (working)
- `prt_src/tui/widgets/progress_indicator.py` - Custom widget (not working)
- `docs/TUI_Dev_Tips.md` - Development patterns learned

### Test Files
- `tests/test_llm_status_checker.py` - Status checker tests (passing)
- `tests/test_chat_progress_indicator.py` - Widget tests (passing but widget doesn't render)

## Lessons Learned

### What Works in PRT TUI
- **Static widget inheritance** for custom widgets
- **Label widgets** for text display (in status bar)
- **RichLog widgets** for chat content
- **Container mounting** in main-container
- **CSS styling** for backgrounds, borders, dimensions

### What Doesn't Work
- **Text content in progress indicator containers** (all approaches fail)
- **Custom widget content rendering** (despite following patterns)
- **Label content updates** in progress indicator context
- **Multiple container strategies** (all create layout issues)

## Conclusion

Despite extensive debugging and multiple approaches, **text content rendering in progress indicator containers remains broken**. The containers mount correctly and styling applies, but all text content (emojis, ASCII, plain text) remains invisible.

This suggests either:
1. **Fundamental Textual framework limitation** in this specific layout context
2. **CSS cascade issue** we haven't identified
3. **Platform-specific rendering bug** 
4. **Layout calculation problem** positioning text outside visible area

**Recommendation**: Consider alternative implementation approaches that don't rely on separate progress indicator containers.

---

*Last updated: 2025-09-17*
*Investigation ongoing*
