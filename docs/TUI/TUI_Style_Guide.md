# PRT Text UI Style Guide

## 1. Core Principles

Follow the Spec First: The TUI_Specification.md should be followed, and this document should add clarity to exactly how it should be laid out and implemented.

Simplicity Second: This is as close to a CLI as possible while still implementing TUI features that speed navigation and use.  Unless needed or specified: No extra containers.  No extra formatting.  No extra whitespace.

Keyboard-Centric: All actions must be achievable via keystrokes. Mouse support optional, never required.

Human-first Efficiency: Optimize for clarity and speed. Make frequent actions simple, but don’t sacrifice readability or guidance.

Consistency & Composability: Use predictable keybindings, flag patterns, and outputs. Ensure output can be piped into scripts or reused downstream.

No Dead Ends: Always provide a universal escape/cancel key (Esc or q).

UX Flow is a Search → Select → Act Loop: Everything should fit into this repeatable cycle:
 - Search/filter long list.
 - Select one or many.
 - Trigger an action.

## 2. Layout & Display

Minimum formatting complexity.  Except where we require a dropdown, a frame, or a container, etc. we keep those out of the equation.  Never include extra services or options or TUI settings that are not in the spec.

Multi-pane Navigation: Use multiple panes (categories, items, preview/details) for orientation, in views where it is useful.

Scannable Tables: Present result data in dense, aligned tables. Support pagination and scrolling.

Visual Encoding: Use restrained colors (green = success, red = error, yellow = warning) and symbols (+ added, ~ modified). Disable colors in non-interactive shells.

## 3. Navigation & Selection

Modal Interaction is to be used when necessary.

Fuzzy Search: Instant fuzzy-finding with real-time filtering for long lists.

Batch Selection: Space/Tab to toggle items into selection. Commands for "select all" / "invert selection."

Single-Key Actions: Map menu items or common verbs (a=add, d=delete, e=edit) to single keys. Use modifiers (Ctrl/Alt) for rarer/destructive actions.  Consistent keys assigned to menu items throughout the UI where possible.

### Terminal Text Input Key Bindings

**Multi-line Text Entry Solution**: We use `Ctrl+J` to insert carriage returns (newlines) within TextArea widgets, while `Enter` executes the primary action.

**Technical Background**:
- In Textual TUI applications, the `Key` event class does not include modifier state attributes (`shift`, `ctrl`, `meta`) that are available in `MouseEvent` classes
- Modifier keys for keyboard events are encoded in the key string itself (e.g., "shift+home", "ctrl+p", "ctrl+j")
- Many terminal emulators do not distinguish between `Enter` and `Shift+Enter`, sending identical escape codes for both key combinations
- This is a fundamental terminal protocol limitation, not a Textual framework issue
- However, `Ctrl+J` is reliably detectable across terminal emulators

**Standard Key Bindings for TextArea Widgets**:
- **Enter**: Execute primary action (send message, execute search, submit form)
- **Ctrl+J**: Insert carriage return (newline) in the text area
- **Esc**: Toggle between NAV and EDIT modes (global binding)

**Hint Text Requirement**: All TextArea widgets MUST display a hint below the input box to remind users of these key bindings:
```
"Enter to send, Ctrl+J inserts carriage return"
```

**Implementation Pattern**:
```python
# Custom TextArea subclass that intercepts keys
class ChatTextArea(TextArea):
    async def _on_key(self, event: events.Key) -> None:
        key = event.key

        # Ctrl+J = insert newline
        if key == "ctrl+j":
            self.insert("\n")
            event.prevent_default()
            event.stop()
            return

        # Enter = submit/execute
        if key == "enter" and self._parent_screen:
            await self._parent_screen._handle_textarea_submit()
            event.prevent_default()
            event.stop()
            return

        # All other keys - let TextArea handle
        await super()._on_key(event)
```

**Hint Text Display**:
```python
# In screen's compose() method, after the TextArea:
self.input_hint = Static(
    "Enter to send, Ctrl+J inserts carriage return",
    id="input-hint",
)
yield self.input_hint
```

**CSS Styling for Hint Text**:
```css
#chat-input-hint, #search-input-hint {
    height: 1;
    color: $text-muted;
    text-style: dim;
}
```

**Rationale**: Using Ctrl+J provides reliable multi-line entry while keeping Enter for the most common action (submit). The hint text ensures discoverability of this non-obvious key combination.

**Reference**: See Textual source code `EXTERNAL_DOCS/textual/src/textual/events.py` lines 260-310 for `Key` event class definition.

### TextArea Input Widget Standards

**Placeholder Text**: All TextArea widgets that accept user input MUST use the `placeholder` parameter instead of setting initial text content.

**Correct Implementation**:
```python
# Use placeholder parameter
self.search_input = TextArea(
    id="search-input",
    placeholder="Enter search text...",
)
```

**Incorrect Implementation**:
```python
# DO NOT set placeholder as initial text content
self.search_input = TextArea(
    "Enter search text...",  # WRONG - this becomes actual content
    id="search-input",
)
```

**Behavior Requirements**:
- Placeholder text MUST disappear immediately when the user types the first character
- Placeholder text MUST reappear if the user deletes all content
- Placeholder text is styled differently (grayed out) to distinguish it from actual content
- When validating input, check for empty/whitespace strings, NOT for the placeholder text value

**Rationale**: Using the `placeholder` parameter ensures Textual's native placeholder handling, which automatically manages visibility and styling. Setting placeholder text as initial content creates bugs where the placeholder persists after typing begins.

### Keyboard Shortcut Display Standards

**Visual Convention**: All keyboard shortcuts MUST be visually indicated in the UI using one of two patterns:

**CRITICAL: Reserved Global Keys** - These keys are NEVER reassigned:
- `esc` - Toggle Nav/Edit modes (Bottom Nav)
- `n` - Toggle dropdown menu (Top Nav)
- `x` - Exit application (Bottom Nav)
- `?` - Help screen (Bottom Nav)
- `h` - Home (Dropdown Menu)
- `b` - Back (Dropdown Menu)

These keys must remain consistent across ALL screens and CANNOT be used for screen-specific menu items.

1. **Letter-based shortcuts** (preferred):
   - Format: `(L)abel` or `La(b)el` where the letter in parens is the key to press
   - Use the first letter when possible, but avoid reserved keys
   - Examples: `(C)hat`, `(S)earch`, `Se(t)tings` (t used because s is taken by Search)
   - When first letter is reserved or conflicts, use another distinctive letter

2. **Number-based shortcuts** (for lists with conflicting letters):
   - Format: `(N) Label` where N is 1-9
   - Use when multiple items share the same first letter OR conflict with reserved keys
   - Must be consistent within a grouping - if one item needs numbers, ALL items in that list use numbers
   - Examples: `(1) Contacts`, `(2) Relationships`, `(3) Relationship Types`, `(4) Notes`, `(5) Tags`

**Implementation Rules**:
- NEVER reassign reserved global keys (esc, n, x, ?, h, b)
- Every selectable menu item must show its shortcut key
- Within a single screen or menu, use either ALL letters OR ALL numbers - never mix
- Shortcuts only work in Navigation mode (not Edit mode)
- The visual indicator is mandatory, not optional
- For single-letter shortcuts, the letter must be case-insensitive (works for both 'c' and 'C')

## 4. Actions & Commands

Context-Aware Menus: Where menus are required, actions can adapt to selection type (e.g., product → checkout/discount; customer → edit/contact).

Feedback: After each action, provide immediate, clear feedback in the status bar (e.g., “3 items deleted”). For long jobs, show progress using the same, simple off-the-shelf progress indicator for all long jobs.

## 5. Output & State

Human-Readable Default: Show tables/text first. 

Explicit State Updates: After any action, state changes must be reported as status (e.g., “Inventory reduced: Item #42 now 12 units”).

## 6. Safety

Safe Defaults: Require confirmation for destructive ops unless explicitly overridden.