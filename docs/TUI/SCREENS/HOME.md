# Home Screen Documentation

## Overview

The Home screen is the main entry point for the PRT TUI. It provides simple navigation to the three core features: Chat, Search, and Settings.

## Screen ID

`home`

## Layout

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

## Components

### Top Nav Bar
- **Menu Button**: `(N)av menu closed/open` - Toggles dropdown menu
- **Screen Name**: `HOME`
- **Mode Indicator**: `Mode: Nav` or `Mode: Edit`

### Main Content
Three simple text options displayed as a left-justified list:
- `* Chat - opens chat screen`
- `* Search - opens search screen`
- `* Settings - opens settings screen`

### Dropdown Menu
Overlay menu that appears below Top Nav when `N` key is pressed:
- `(H)ome` - Navigate to home screen (already here)
- `(B)ack` - Navigate back (no-op on home screen)

### Bottom Nav Bar
Key hints and status messages:
- `(esc) Toggle Nav/Edit` - Switch between Navigation and Edit modes
- `(x) Exit` - Exit application
- `(?) Help` - Show help screen
- Status area on right for temporary messages

## Key Bindings

### Navigation Mode

| Key | Action | Notes |
|-----|--------|-------|
| `N` or `n` | Toggle dropdown menu | Opens/closes menu overlay |
| `C` or `c` | Open Chat screen | Phase 2 implementation |
| `S` or `s` | Open Search screen | Phase 2 implementation |
| `T` or `t` | Open Settings screen | Phase 2 implementation |
| `X` or `x` | Exit application | Immediate exit, no confirmation |
| `?` | Show Help screen | Phase 1 implementation |
| `ESC` | Toggle mode | Switch between Nav and Edit modes |

### Dropdown Menu (when open)

| Key | Action | Notes |
|-----|--------|-------|
| `H` or `h` | Home action | Shows status message, closes menu |
| `B` or `b` | Back action | Shows status message, closes menu |

### Edit Mode

In Edit mode, single-key navigation shortcuts are disabled to allow text input in future form fields.

## Implementation Details

### File Location
`prt_src/tui/screens/home.py`

### Class
`HomeScreen(BaseScreen)`

### Dependencies
- `TopNav` - Top navigation bar widget
- `BottomNav` - Bottom status bar widget
- `DropdownMenu` - Menu overlay widget
- `BaseScreen` - Base screen class
- `AppMode` - Mode enumeration

### State Management
- `screen_title`: Always "HOME"
- `top_nav`: TopNav widget instance
- `bottom_nav`: BottomNav widget instance
- `dropdown`: DropdownMenu widget instance

## Behavior

### On Mount
1. Screen renders with all components
2. Dropdown menu is hidden by default
3. Top nav shows "Nav menu closed"
4. Mode indicator reflects current app mode

### Menu Toggle
1. User presses `N` key
2. Dropdown menu visibility toggles
3. Top nav updates to show "Nav menu open/closed"
4. Menu displays over content with overlay layer

### Navigation Actions
1. User presses shortcut key (C, S, T)
2. Action attempts to navigate to target screen
3. If screen not implemented, status message shows
4. Status message: "[Screen] not yet implemented"

### Exit Action
1. User presses `X` key
2. App exit method is called immediately
3. No confirmation dialog (per spec simplicity)

## Status Messages

Temporary messages displayed in bottom nav status area:

- "Already on home screen" - When Home or Back selected from menu
- "Chat screen not yet implemented" - C key pressed
- "Search screen not yet implemented" - S key pressed
- "Settings screen not yet implemented" - T key pressed
- "Help screen navigation pending" - ? key pressed

## Testing

### Test Coverage
- Screen mounting and rendering
- Top/bottom nav presence
- Menu options display
- Dropdown menu presence
- Menu toggle functionality
- Navigation key presses
- Mode awareness
- Dropdown menu actions
- Exit functionality

### Test File
`tests/test_home_screen.py`

### Key Test Cases
1. `test_screen_mounts` - Verify screen mounts successfully
2. `test_has_top_nav` - Verify top nav present with "HOME"
3. `test_has_bottom_nav` - Verify bottom nav present
4. `test_has_menu_options` - Verify 3 menu options displayed
5. `test_toggle_menu_with_n_key` - Verify menu toggle works
6. `test_c_key_attempts_chat_navigation` - Verify C key action
7. `test_x_key_exits_app` - Verify X key exits
8. `test_dropdown_has_home_option` - Verify dropdown menu content
9. `test_keys_only_work_in_nav_mode` - Verify mode awareness

## Future Enhancements

Phase 2 and beyond:
- Actual navigation to Chat, Search, Settings screens
- Help screen integration with H key
- Visual feedback for menu item selection
- Mouse click support for menu items
- Keyboard navigation within dropdown menu (arrow keys)

## Known Issues

None currently. Screen is simple and functional per spec.

## Related Documentation

- [TUI Specification](../TUI_Specification.md) - Overall spec
- [TUI Style Guide](../TUI_Style_Guide.md) - Design principles
- [TUI Key Bindings](../TUI_Key_Bindings.md) - Complete key reference
- [TUI Refactor Plan](../TUI_REFACTOR_PLAN.md) - Implementation plan

## Revision History

- **2025-10-08**: Initial implementation (Phase 1, Issue #120)
