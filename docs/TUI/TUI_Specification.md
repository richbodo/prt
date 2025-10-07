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

Left justified list of options
* Chat - opens chat screen
* Search - opens search screen
* Settings - opens settings screen

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





