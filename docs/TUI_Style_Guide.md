# PRT Text UI Style Guide

These are only guidelines - there is no way we can implement all of this - but it's a good place to start.

## 1. Core Principles

Keyboard First: All actions must be achievable via keystrokes. Mouse support optional, never required.

Human-first Efficiency: Optimize for clarity and speed. Make frequent actions simple, but don’t sacrifice readability or guidance.

Consistency & Composability: Use predictable keybindings, flag patterns, and outputs. Ensure output can be piped into scripts or reused downstream.

No Dead Ends: Always provide a universal escape/cancel key (Esc or q).

## 2. Layout & Display

Multi-pane Navigation: Use multiple panes (categories, items, preview/details) for orientation, in views where it is useful.

Scannable Tables: Present result data in dense, aligned tables. Support pagination and scrolling.

Status Bar: Persistent line showing mode, filters, selections, and top key hints, or location in the menu, etc.

Visual Encoding: Use restrained colors (green = success, red = error, yellow = warning) and symbols (+ added, ~ modified). Disable colors in non-interactive shells.

## 3. Navigation & Selection

Modal Interaction is to be used when necessary.  Most interactions are so simple that modes are not useful, but if we do need modes, then Normal mode = navigation & selection (hjkl, arrows) and Command/Insert mode = text input (/: search, :action).

Fuzzy Search: Instant fuzzy-finding with real-time filtering for long lists.

Batch Selection: Space/Tab to toggle items into selection. Commands for “select all” / “invert selection.”

Single-Key Actions: Map menu items or common verbs (a=add, d=delete, e=edit) to single keys. Use modifiers (Ctrl/Alt) for rarer/destructive actions.  Consistent keys assigned to menu items throughout the UI where possible.

## 4. Actions & Commands

Context-Aware Menus: Actions adapt to selection type (e.g., product → checkout/discount; customer → edit/contact).

Command Palette: Global, searchable menu (Ctrl+Shift+P or :) for less common commands.

Chained Commands: Allow chaining multiple verbs (e.g., select → filter → export).

Feedback: After each action, provide immediate, clear feedback in the status bar (e.g., “3 items deleted”). For long jobs, show progress.

## 5. Flags, Arguments & Help

Predictable Flags: Support both long (--filter) and short (-f) forms.

Smart Help: -h = concise overview; --help = detailed docs with examples. Link to web docs if available.

Error Recovery: Offer suggestions for typos (“Did you mean --output?”).

## 6. Output & State

Human-Readable Default: Show tables/text first. Provide machine-friendly formats (CSV, JSON) on request.

Explicit State Updates: After any action, state changes must be reported (e.g., “Inventory reduced: Item #42 now 12 units”).

Status Command: Quick command (status) to show current state, pending actions, and next logical steps.

## 7. Extra Niceties

Progress Indicators: For long DB processes, show spinners or percentage.

Safe Defaults: Require confirmation for destructive ops unless explicitly overridden.

Feedback Channels: Provide easy way for users to report issues (help → feedback).

ASCII Art - is fun, but leave it off for now.  This is something like "themes" that can be implemented and turned off/on by users.

## Special Notes for POS/Inventory Workflows

Search → Select → Act Loop: Everything should fit into this repeatable cycle:

Search/filter long list.

Select one or many.

Trigger an action.

Bulk Operations: Always allow batch processing (e.g., apply discount to multiple items).

Performance: Filtering, searching, and rendering must feel instantaneous — long delays break the flow.
