# TUI Specification for Personal Relationship Tracker (PRT)

## Overview

This document defines the expected behavior, navigation flow, and screen specifications for the PRT Text User Interface (TUI). The TUI is built with Textual and implements a modern, keyboard-first contact management interface.

## Application Flow

### First Run vs Existing Installation
- **First Run**: Shows `wizard` screen to create "You" contact and optional demo data
- **Existing Installation**: Goes directly to `home` screen

### Mode System
- **Navigation Mode**: Default mode for browsing and selection (j/k navigation, single-key actions)
- **Edit Mode**: Text input mode for forms and search (ESC toggles back to navigation)

## Screen Specifications

### 1. Home Screen (`home`)
**Purpose**: Main navigation hub with menu-driven interface
**Layout**: Centered welcome message with navigation menu below
**Navigation**:
- **Key Bindings**: `c` (Contacts), `s` (Search), `r` (Relationships), `y` (Rel. Types), `i` (Import), `e` (Export), `d` (Database), `m` (Metadata), `t` (Chat), `?` (Help), `q` (Quit)
- **ESC Behavior**: Does nothing (no dead ends)
- **Entry Points**: App startup (existing installation), returning from other screens

### 2. Wizard Screen (`wizard`)
**Purpose**: First-run setup wizard for new installations
**Layout**: Multi-step wizard with welcome, "You" contact creation, and options
**Navigation**:
- **Steps**: Welcome → Create "You" Contact → Options → Complete
- **Key Bindings**: `Enter` (continue), `ESC` (skip/back depending on step)
- **ESC Behavior**: Custom handling per step (skip setup or go home)
- **Entry Points**: App startup (first run only)

### 3. Contacts Screen (`contacts`)
**Purpose**: Browse and manage contacts in a data table
**Layout**: DataTable with columns for Name, Email, Phone, Last Interaction
**Navigation**:
- **Key Bindings**: `a` (add), `e` (edit), `d` (delete), `Enter` (view details), `/` (search), `ESC` (back)
- **ESC Behavior**: POP (return to previous screen)
- **Entry Points**: Home screen, search results, relationship management
- **Modes**: View mode (default), Search mode (with `/` key)

### 4. Search Screen (`search`)
**Purpose**: Full-text search with scope filters and export capabilities
**Layout**: Search input at top, filters on left, results on right
**Navigation**:
- **Key Bindings**: `/` (focus search), `Tab` (cycle filters), `Enter` (select result), `ESC` (back)
- **ESC Behavior**: POP if showing results, HOME if empty search
- **Entry Points**: Home screen, contacts screen search mode
- **Modes**: Search input mode, Results browsing mode

### 5. Relationships Screen (`relationships`)
**Purpose**: View and manage contact relationships in a data table
**Layout**: DataTable showing Person 1, Relationship Type, Person 2, Start Date, Status
**Navigation**:
- **Key Bindings**: `a` (add), `e` (edit), `d` (delete), `Enter` (view), `ESC` (back)
- **ESC Behavior**: POP (return to previous screen)
- **Entry Points**: Home screen, contact detail screens

### 6. Relationship Types Screen (`relationship_types`)
**Purpose**: Manage available relationship types (family, friend, colleague, etc.)
**Layout**: List of relationship types with management options
**Navigation**:
- **Key Bindings**: `a` (add), `e` (edit), `d` (delete), `ESC` (back)
- **ESC Behavior**: POP (return to previous screen)
- **Entry Points**: Home screen, relationship creation flows

### 7. Database Screen (`database`)
**Purpose**: Database management with game-style backup slots
**Layout**: Statistics at top, backup slots below with restore options
**Navigation**:
- **Key Bindings**: `b` (backup), `r` (restore), `e` (export), `i` (import), `v` (vacuum), `ESC` (back)
- **ESC Behavior**: POP (return to previous screen)
- **Entry Points**: Home screen

### 8. Contact Detail Screen (`contact_detail`)
**Purpose**: View detailed information about a specific contact
**Layout**: Contact information with related relationships and notes
**Navigation**:
- **Key Bindings**: `e` (edit), `r` (relationships), `ESC` (back)
- **ESC Behavior**: POP (return to contacts list or previous screen)
- **Entry Points**: Contacts screen, search results, relationship views

### 9. Contact Form Screen (`contact_form`)
**Purpose**: Add or edit contact information
**Layout**: Form fields for contact details with validation
**Navigation**:
- **Key Bindings**: `Tab` (next field), `Shift+Tab` (previous field), `Enter` (save), `ESC` (cancel)
- **ESC Behavior**: CONFIRM (show discard dialog if changes made)
- **Entry Points**: Contacts screen (add/edit), contact detail screen (edit)

### 10. Relationship Form Screen (`relationship_form`)
**Purpose**: Create or edit relationships between contacts
**Layout**: Dual contact selector with relationship type picker
**Navigation**:
- **Key Bindings**: `Tab` (cycle selections), `Enter` (save), `ESC` (cancel)
- **ESC Behavior**: CONFIRM (show discard dialog if changes made)
- **Entry Points**: Relationships screen, contact detail screen

### 11. Import Screen (`import`)
**Purpose**: Import contacts from various sources (Google Takeout, CSV, etc.)
**Layout**: Import source selection with preview and options
**Navigation**:
- **Key Bindings**: File selection and import options, `ESC` (back)
- **ESC Behavior**: POP (return to previous screen)
- **Entry Points**: Home screen, database screen

### 12. Export Screen (`export`)
**Purpose**: Export contacts and relationships in various formats
**Layout**: Export format selection with filtering options
**Navigation**:
- **Key Bindings**: Format selection (`c` CSV, `v` VCard, `j` JSON), `ESC` (back)
- **ESC Behavior**: POP (return to previous screen)
- **Entry Points**: Home screen, search results, contacts screen

### 13. Metadata Screen (`metadata`)
**Purpose**: Manage tags and notes associated with contacts
**Layout**: Tag and note management interface
**Navigation**:
- **Key Bindings**: Tag/note management actions, `ESC` (back)
- **ESC Behavior**: POP (return to previous screen)
- **Entry Points**: Home screen

### 14. Chat Screen (`chat`)
**Purpose**: Natural language interface for querying and managing contacts
**Layout**: Chat history with input field and results preview
**Navigation**:
- **Key Bindings**: Natural language input, command shortcuts, `ESC` (back)
- **ESC Behavior**: POP (return to previous screen)
- **Entry Points**: Home screen

## Navigation Patterns

### Navigation Stack
- Uses NavigationService to maintain screen history
- ESC behavior varies by screen intent (POP, HOME, CONFIRM, CUSTOM, CANCEL)
- Supports breadcrumb navigation for complex workflows

### Universal Keybindings
- **ESC**: Context-dependent navigation (never a dead end)
- **?**: Help (global binding)
- **q**: Quit (navigation mode only)
- **Mode Toggle**: ESC toggles between Navigation and Edit modes

### Search Integration
- **Global Search**: Available from most screens via `/` key
- **Contextual Search**: Within lists and tables for filtering
- **Autocomplete**: Powered by centralized AutocompleteEngine

## Current Issues Identified

### 1. Dead End Problem
**Issue**: Starting page may lack clear navigation back to main menu
**Solution**: Ensure home screen is always accessible and provides clear navigation options

### 2. Mode Confusion
**Issue**: Users may not understand Navigation vs Edit mode distinction
**Solution**: Clear mode indicators in header/footer and consistent ESC behavior

### 3. Navigation Consistency
**Issue**: Different screens may handle ESC and navigation differently
**Solution**: Standardize ESC intents and ensure all screens implement proper navigation

## Design Principles

### 1. Keyboard First
- All actions achievable via keystrokes
- Single-key actions for common operations
- Consistent keybindings across screens

### 2. No Dead Ends
- Every screen provides clear navigation out
- ESC key always provides meaningful action
- Home screen always accessible

### 3. Search → Select → Act
- Consistent workflow pattern across screens
- Fuzzy search and autocomplete where applicable
- Batch operations supported

### 4. Modal Clarity
- Clear distinction between Navigation and Edit modes
- Mode indicators in UI
- Consistent mode switching behavior

### 5. Progressive Disclosure
- Simple interfaces with advanced options available
- Context-sensitive help and hints
- Logical information hierarchy

## Technical Implementation Notes

### Screen Registration
- All screens register themselves in `SCREEN_REGISTRY`
- Factory pattern for screen creation with service injection
- Lazy loading and error handling for development

### Service Architecture
- NavigationService: Screen stack and routing
- DataService: Business logic abstraction
- NotificationService: User feedback and alerts
- SelectionService: Multi-select operations (Phase 2)
- ValidationService: Form validation (Phase 2)

### State Management
- Screen-specific state maintained in screen instances
- Global app state for mode and navigation
- Persistent selections across pagination

This specification serves as the definitive guide for TUI behavior and should be updated as screens are implemented and refined.
