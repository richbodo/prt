# TUI Specification for Personal Relationship Tracker (PRT)

## Overview

This document defines the expected behavior, navigation flow, and screen specifications for the PRT Text User Interface (TUI). The TUI is built with Textual and implements a modern, keyboard-first contact management interface.

## Application Flow

### First Run vs Existing Installation
- **First Run**: Shows `wizard` screen to create "You" contact and optional demo data
- **Existing Installation**: Goes directly to `home` screen

### Mode System
- **Navigation Mode**: Default mode for browsing and selection (j/k navigation, single-key actions)
- **Edit Mode**: Text input mode for forms and search

#### Mode Switching Behavior

When ESC is pressed to toggle between NAV and EDIT modes:

**Smart Mode Toggle**: The application automatically detects whether editable widgets (TextArea, Input) exist on the current screen before allowing mode changes.

**On screens WITH edit boxes** (Chat, Search):
- Any open dropdown menu closes automatically
- Mode switches to EDIT
- Cursor automatically focuses in the first/primary edit box
- User can immediately start typing
- The blinking cursor appears in the focused input box

**On screens WITHOUT edit boxes** (Home, Settings, Help):
- Attempting to switch to EDIT mode is blocked
- Status message appears: "No editable fields on this screen"
- Mode remains as NAV (does not change)
- This prevents "fake" mode changes where EDIT mode would have no effect

**Returning from EDIT to NAV**:
- ESC toggles back to NAV mode (always works)
- Any focused input widgets are automatically blurred
- Keyboard input now triggers single-key shortcuts instead of text entry

**Implementation Requirements**:
- BaseScreen provides `has_editable_widgets()` method that auto-detects TextArea and Input widgets
- App's `action_toggle_mode()` checks this method before allowing switch to EDIT mode
- Screens with input boxes MUST override `on_mode_changed(mode)` from BaseScreen
- When mode changes to EDIT, screens MUST call `.focus()` on their primary input widget
- The mode change notification happens automatically via the app's `action_toggle_mode()`
- This ensures consistent "focus on EDIT" behavior across all screens

**Design Rationale**: Mode indicators should reflect actual capability. If EDIT mode provides no different functionality than NAV mode, the UI should not claim to be in EDIT mode. This creates honest feedback and prevents user confusion.

### Keyboard Shortcut Display Conventions

All keyboard shortcuts for menu items and navigation must be clearly indicated using a consistent visual pattern:

**Reserved Global Keys** (NEVER change these):
- `(esc)` - Toggle between Nav/Edit modes (Bottom Nav)
- `(n)` - Toggle dropdown menu (Top Nav)
- `(x)` - Exit application (Bottom Nav)
- `(?)` - Help screen (Bottom Nav)
- `(h)` - Home (Dropdown Menu)
- `(b)` - Back (Dropdown Menu)

These keys are reserved and consistent across ALL screens. Do not use these letters for any other purpose.

**Letter-based shortcuts** (preferred when possible):
- Use parentheses around a letter in the word: `(C)hat`, `(S)earch`, `Se(t)tings`
- Prefer the first letter, but use another letter if the first is reserved or conflicts
- The letter inside parentheses is the key to press in Navigation mode
- Examples: `(C)hat`, `(S)earch`, `Se(t)tings` (t instead of s which is taken)

**Number-based shortcuts** (for lists with conflicting letters):
- Use numbers 1-9 in parentheses before the item name: `(1) Contacts`, `(2) Relationships`
- Start numbering at 1 for the first item and increment sequentially
- Examples: `(1) Contacts`, `(2) Relationships`, `(3) Relationship Types`, `(4) Notes`, `(5) Tags`

**Consistency rules**:
- NEVER reassign reserved global keys (esc, n, x, ?, h, b)
- If ANY items in a list have conflicting letters (including reserved keys), use numbers for ALL items in that list
- Keep the same shortcut style (letters or numbers) within each logical grouping
- Always show the shortcut indicator, even if it seems obvious
- The shortcut key only works in Navigation mode (not Edit mode)

**Examples**:

Good - All letter-based (no conflicts):
```
(C)hat
(S)earch
(T)ools
```

Good - All number-based (conflicts resolved):
```
(1) Contacts
(2) Colleagues
(3) Categories
```

Bad - Inconsistent mixing:
```
(C)hat
(2) Search
(T)ools
```

## Bottom Nav (aka Status Bar)

Bottom Nav is a single line high.  Three options are present on the bottom nav, left justified:

(esc) Toggle Nav/Edit modes
(x) Exit Application
(?) Help

Esc always works to change modes.  When in Nav mode, the other two work as well.

To the right of those options, status text can be displayed as actions are taken by any screen.

## Top Nav (aka Menu Bar)

The Top Nav Menu Bar is a single line menu bar, always present at the top of each screen in the app UI.  

Left justified, it has a drop down menu.  The drop down menu is described in the next section. 

To the right of that, in the same single line top menu bar, is the name of the screen the user is currently on, i.e. HOME.  To the right of that, a mode indicator is shown as a text string.  The only mode text strings are: "Mode: Edit" or "Mode: Nav"

### Drop down menu on Top Nav

The drop down menu, in the furthest upper left corner of the screen, instead of an icon, is identified by a text string: when closed the text reads "(N)av menu closed", and when open "(N)av menu open".  When in Nav mode, the letter N toggles the menu.  If the user presses "N" or "n" or clicks on the text string in the upper left corner, them menu opens or closes.

The items on the menu are:

(H)ome - go to the home screen
(B)ack - go back to the previous screen

## Screen Specifications

There are currently only five screens supported by the TUI

### Home

Left justified list of options:
* (C)hat - opens chat screen
* (S)earch - opens search screen
* Se(t)tings - opens settings screen

### Chat

Chat Status Line: The line immediately below the Top Nav, in the Chat Screen, is called the Chat Status Line.  The Chat Status Line displays the following two items, from left to right, which are controlled by background processes:

1) LLM availability: Shows the status of our connection with the LLM
✅ "LLM: Online" (green)
❌ "LLM: Offline" (red)
⚠️ "LLM: Checking..." (yellow)

2) LLM progress: Shows a progress indicator.  When the LLM is not processing a prompt, it either shows READY, or ERROR.

Chat Box: When opened, the chat window displays a top-justified edit box for the user to type prompts into. That is called the "chat box".  This is a few lines high, but scrollable, with a usable scrollbar on the right for mouse users.  When a user hits enter in the chat box, it sends the prompt to the LLM.  When the user hits "Shift+Enter" key combo, it sends a carraige return to the edit box, moving to the next line.

Response Box: Below the Chat Box, a text display box shows the responses of the LLM to user prompts.  It is also scrollable and contains the last 64KB of responses.

### Search

This screen implements the Search part of the "Search-Select-Act" loop, and does not allow for selection or action, yet.

Search Edit Box: The line immediately below the top nav, on the Search Screen, shows a three line edit box called the Search Edit Box.  This is for entering a free-form text string to search on.

Search Dropdown:  Below the Search Edit Box, are five search buttons, which correspond to the five user-editable data types in the db.  The mouse can be used to select a button, or when in nav mode, the number of the item selected can be pressed on the keyboard: 
(1) Contacts
(2) Relationships
(3) Relationship_Types
(4) Notes
(5) Tags

Search Results Box: A scrollable text box.  Search returns all of the items of the data type corresponding to the button pressed, that match the string entered into the search edit box.  No pagination.  No nav.  Just a simple list for now.

Future implementation: Do not implement, yet: All editing functions will begin with the search screen - CRUD any user editable data type.  Subfilter searches, pagination, and additional nav is all future development.  Exporting graphs are also future development items.

### Settings

Database Status Line: A single line below the Top Nav.  Shows db connection status and the number of rows of each user-searchable data type present in the db.

Future implementation: Do not implement, yet: Import Contacts, Export Database.

### Help

For now, this just shows a single line of text: "Help not implemented yet."





