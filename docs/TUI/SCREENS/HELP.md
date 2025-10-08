# Help Screen Documentation

## Overview

The Help screen is a simple placeholder screen that will eventually display comprehensive help information. Currently shows a single line message per the simplified TUI specification.

## Screen ID

`help`

## Layout

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

## Components

### Top Nav Bar
- **Menu Button**: `(N)av menu closed/open` - Would toggle dropdown menu (not implemented on this screen)
- **Screen Name**: `HELP`
- **Mode Indicator**: `Mode: Nav` or `Mode: Edit`

### Main Content
Single line of text:
- `Help not implemented yet.`

### Bottom Nav Bar
Standard key hints and status messages:
- `(esc) Toggle Nav/Edit` - Switch between Navigation and Edit modes
- `(x) Exit` - Exit application
- `(?) Help` - Show help screen (already here)
- Status area on right for temporary messages

## Key Bindings

### Navigation Mode

| Key | Action | Notes |
|-----|--------|-------|
| `ESC` | Return to previous screen | Standard back navigation |
| `X` or `x` | Exit application | Immediate exit |

### Edit Mode

Not applicable for this screen (no input fields).

## Implementation Details

### File Location
`prt_src/tui/screens/help.py`

### Class
`HelpScreen(BaseScreen)`

### Dependencies
- `TopNav` - Top navigation bar widget
- `BottomNav` - Bottom status bar widget
- `BaseScreen` - Base screen class

### State Management
- `screen_title`: Always "HELP"
- `top_nav`: TopNav widget instance
- `bottom_nav`: BottomNav widget instance

## Behavior

### On Mount
1. Screen renders with all components
2. Top nav shows "HELP" as screen name
3. Single placeholder message displays
4. Mode indicator reflects current app mode

### Navigation
Standard ESC key handling inherited from BaseScreen:
1. User presses `ESC` key
2. Screen pops from navigation stack
3. Returns to previous screen (typically Home)

## Status Messages

No custom status messages for this screen. Uses standard bottom nav hints.

## Testing

### Test Coverage
- Screen mounting and rendering
- Top/bottom nav presence
- Placeholder message display
- ESC key navigation (inherited from BaseScreen)

### Test File
`tests/test_help_screen.py`

### Key Test Cases
1. `test_screen_mounts` - Verify screen mounts successfully
2. `test_has_top_nav` - Verify top nav present with "HELP"
3. `test_has_bottom_nav` - Verify bottom nav present
4. `test_displays_placeholder_message` - Verify placeholder text shown
5. `test_esc_returns_to_previous_screen` - Verify back navigation

## Future Enhancements

Future implementations should include:

### Content Structure
- **Key Bindings Reference**: Complete list of all keybindings by screen
- **Navigation Guide**: How to move between screens
- **Mode System**: Explanation of Nav vs Edit modes
- **Feature Overview**: Brief description of each feature
- **Troubleshooting**: Common issues and solutions
- **Version Information**: App version and build info

### UI Improvements
- **Scrollable Content**: For longer help text
- **Sections**: Collapsible sections for different topics
- **Search**: Ability to search help content
- **Context-Aware Help**: Show help for current screen
- **Examples**: Visual examples of workflows

### Implementation Considerations
- Use `RichLog` or scrollable `Static` widget for content
- Load help content from markdown files
- Support for syntax highlighting in code examples
- Keyboard shortcuts for section navigation

## Known Issues

None currently. Screen is intentionally minimal per spec.

## Related Documentation

- [TUI Specification](../TUI_Specification.md) - Overall spec
- [TUI Style Guide](../TUI_Style_Guide.md) - Design principles
- [TUI Key Bindings](../TUI_Key_Bindings.md) - Complete key reference
- [TUI Refactor Plan](../TUI_REFACTOR_PLAN.md) - Implementation plan
- [Home Screen](HOME.md) - Home screen documentation

## Revision History

- **2025-10-08**: Initial implementation (Phase 1, Issue #120)
