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

Batch Selection: Space/Tab to toggle items into selection. Commands for “select all” / “invert selection.”

Single-Key Actions: Map menu items or common verbs (a=add, d=delete, e=edit) to single keys. Use modifiers (Ctrl/Alt) for rarer/destructive actions.  Consistent keys assigned to menu items throughout the UI where possible.

## 4. Actions & Commands

Context-Aware Menus: Where menus are required, actions can adapt to selection type (e.g., product → checkout/discount; customer → edit/contact).

Feedback: After each action, provide immediate, clear feedback in the status bar (e.g., “3 items deleted”). For long jobs, show progress using the same, simple off-the-shelf progress indicator for all long jobs.

## 5. Output & State

Human-Readable Default: Show tables/text first. 

Explicit State Updates: After any action, state changes must be reported as status (e.g., “Inventory reduced: Item #42 now 12 units”).

## 6. Safety

Safe Defaults: Require confirmation for destructive ops unless explicitly overridden.