# TUI Key Bindings Specification for PRT

## Key Binding Architecture

### Event Flow Hierarchy
1. **Screen Level**: Each screen's `on_key()` method handles keys first
2. **Widget Level**: Screens delegate to widgets (e.g., NavigationMenu, DataTable)
3. **App Level**: Unhandled keys fall back to app-level `BINDINGS` and `on_key()`
4. **System Level**: Textual framework handles remaining keys

### Key Event Processing Order
```
User Presses Key
    ↓
Screen.on_key() 
    ↓
Widget.handle_key() (if delegated)
    ↓
App.on_key() (if not handled by screen/widget)
    ↓
App.BINDINGS (if not handled by on_key)
    ↓
Textual System (if not handled)
```

## App-Level Key Bindings

### Global Bindings (PRTApp.BINDINGS)
- **`ESC`** → `toggle_mode` - Toggle between Navigation/Edit modes (priority=True)
- **`q`** → `quit` - Quit application (show=False, only in NAV mode)  
- **`x`** → `exit_with_confirmation` - Exit with Y/N confirmation (priority=True) (this is a temporary debugging aid)
- **`?`** → `help` - Show help screen

### App-Level Key Handler (PRTApp.on_key)
- **`escape`** → Manual handling via `handle_escape()`
- **`q`** → Manual handling via `action_quit()` 
- **`x`** → Manual handling via `action_exit_with_confirmation()`
- **`question_mark`** → Manual handling via `action_help()`

## Screen-Specific Key Bindings

### Home Screen (`home`)
**Navigation Menu Items** (handled by NavigationMenu widget):
- **`c`** → Navigate to Contacts screen
- **`r`** → Navigate to Relationships screen  
- **`y`** → Navigate to Relationship Types screen
- **`s`** → Navigate to Search screen
- **`i`** → Navigate to Import screen
- **`e`** → Navigate to Export screen
- **`d`** → Navigate to Database screen
- **`m`** → Navigate to Metadata screen
- **`t`** → Navigate to Chat screen
- **`x`** → Exit with confirmation
- **`?`** → Show help
- **`q`** → Quit application

**Navigation Menu Controls**:
- **`j`** → Move down in menu (vim-style)
- **`k`** → Move up in menu (vim-style)
- **`G`** → Go to last menu item
- **`g`** → Go to first menu item  
- **`Enter`** → Activate selected menu item

**Footer Hints**: `[c] Contacts`, `[s] Search`, `[r] Relationships`, `[y] Rel. Types`, `[i] Import`, `[e] Export`, `[d] Database`, `[m] Metadata`, `[t] Chat`, `[x] Exit`, `[?] Help`, `[q] Quit`

### Contacts Screen (`contacts`)
**Footer Hints**: `[a]dd`, `[e]dit`, `[d]elete`, `[Enter] View`, `[/] Search`, `[ESC] Back`

**DataTable Navigation**:
- **Arrow keys** → Navigate table rows
- **Enter** → View contact details
- **`/`** → Switch to search mode

### Search Screen (`search`)
**Footer Hints**: `[/] Focus search`, `[Tab] Cycle filters`, `[Enter] Select result`, `[ESC] Back`

**Search Controls**:
- **`/`** → Focus search input
- **Tab** → Cycle through scope filters
- **Enter** → Select search result

### Relationships Screen (`relationships`)
**Footer Hints**: `[a]dd`, `[e]dit`, `[d]elete`, `[Enter] View`, `[ESC] Back`

### Relationship Types Screen (`relationship_types`)
**Footer Hints**: `[a]dd`, `[e]dit`, `[d]elete`, `[Enter] View`, `[ESC] Back`

### Contact Detail Screen (`contact_detail`)
**Footer Hints**: `[e]dit`, `[d]elete`, `[Enter] Back`, `[ESC] Back`

### Contact Form Screen (`contact_form`)
**Footer Hints**: `[Ctrl+S] Save`, `[Ctrl+C] Cancel`, `[Tab] Next field`, `[Shift+Tab] Previous field`, `[ESC] Cancel`

### Relationship Form Screen (`relationship_form`)
**Footer Hints**: `[Ctrl+S] Save`, `[Ctrl+C] Cancel`, `[Tab] Next field`, `[Shift+Tab] Previous field`, `[ESC] Cancel`

### Database Screen (`database`)
**Footer Hints**: `[b]ackup`, `[r]estore`, `[e]xport`, `[i]mport`, `[v]acuum`, `[ESC] Back`

### Import Screen (`import`)
**State-dependent hints**:
- **In Progress**: `Import in progress...`
- **Complete**: `[h]ome`, `[c]ontacts`, `[ESC] Back`
- **Default**: `[i]mport`, `[p]review`, `[ESC] Back`

### Export Screen (`export`)
**State-dependent hints**:
- **In Progress**: `Export in progress...`
- **Complete**: `[o]pen folder`, `[e]xport another`, `[ESC] Back`
- **Default**: `[e]xport`, `[ESC] Back`

### Metadata Screen (`metadata`)
**Mode-dependent hints**:
- **Tags Mode**: `[Tab] Switch`, `[a]dd tag`, `[e]dit tag`, `[d]elete tag`, `[ESC] Back`
- **Notes Mode**: `[Tab] Switch`, `[a]dd note`, `[e]dit note`, `[d]elete note`, `[ESC] Back`

### Wizard Screen (`wizard`)
**Step-dependent hints**:
- **Welcome**: `[Enter] Continue`, `[ESC] Skip Setup`
- **Create You**: `[Enter] Create`, `[ESC] Skip`
- **Options**: `[Enter] Select`, `[ESC] Skip`
- **Complete**: `[Enter] Continue to PRT`

### Chat Screen (`chat`)
**Chat-specific controls**:
- **Enter** → Send message
- **Up/Down arrows** → Navigate chat history
- **ESC** → Back to previous screen

## Key Binding Status Analysis

### ✅ Working Key Bindings
- **`ESC`** → Mode toggle and screen navigation (works everywhere)
- **`q`** → Quit (works via navigation menu in home screen)
- **`?`** → Help (works, triggers help action)
- **Navigation menu keys** → `c`, `r`, `y`, `s`, `i`, `e`, `d`, `m`, `t` (work via menu selection)
- **Vim navigation** → `j`, `k`, `g`, `G` (work in navigation menu)
- **`Enter`** → Activate selected items (works in menus and tables)

### ❌ Non-Working Key Bindings  
- **`x`** → Exit confirmation (triggers action but no visible dialog)
- **Direct key shortcuts** → Keys like `c`, `s`, `r` don't work as direct shortcuts (only via menu)

### 🔍 Key Binding Issues Identified

1. **App-level bindings don't work** when screens have `on_key()` methods
2. **Screen `on_key()` methods intercept** all keys before app bindings
3. **Navigation menu consumes** most single-letter keys via `select_by_key()`
4. **Confirmation dialogs not implemented** - actions trigger but no UI feedback

## Key Event Interception Points

### Home Screen Key Flow
```
User presses 'x'
    ↓
HomeScreen.on_key('x') 
    ↓
NavigationMenu.handle_key('x') 
    ↓ 
NavigationMenu.select_by_key('x') → Finds "Exit" menu item → Activates
    ↓
HomeScreen._handle_menu_activation(MenuItem("x", "Exit", ...))
    ↓
app.action_exit_with_confirmation() → Logs but no dialog
```

### Other Screen Key Flow
```
User presses 'x' (on non-home screen)
    ↓
[Screen].on_key('x')
    ↓
super().on_key('x') → May not reach app level properly
    ↓
App.on_key('x') → Should trigger but might not be reached
```

## Recommendations

### 1. Fix Key Event Propagation
- Ensure all screen `on_key()` methods properly delegate unhandled keys to app level
- Consider removing screen-level `on_key()` for non-essential keys

### 2. Implement Missing Dialogs
- **Exit confirmation dialog** with Y/N keys
- **Discard confirmation dialog** for form screens

### 3. Standardize Key Handling
- Create consistent patterns for screen-specific vs app-level keys
- Document which keys should be handled at which level

### 4. Add Missing Functionality
- Implement help screen (currently just logs)
- Add proper modal dialog system
- Ensure all advertised key hints actually work

## Current Working Exit Methods
1. **Mouse click on "🚪 Quit" menu item** → Works, exits immediately
2. **Mouse click on "❌ Exit" menu item** → Triggers action but no dialog shown
3. **`q` key** → Works via navigation menu → quit action
4. **`x` key** → Triggers action but no dialog shown

The `X` key binding is technically working (logs show it triggers), but the confirmation dialog implementation is missing.
