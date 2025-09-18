# 🎬 Visual Demo: Textual Debug Workflow in Action

## 📺 Terminal Setup (2 terminals side by side)

```
┌─────────────────────────────────┐ ┌─────────────────────────────────┐
│ TERMINAL 1: Debug Console       │ │ TERMINAL 2: Demo App            │
│ $ textual console --port 7342   │ │ $ textual run --dev --port 7342 │
│                                 │ │   textual_debug_demo.py         │
│ 🖥️  Textual Console Started     │ │                                 │
│ ✅ Listening on port 7342       │ │ 🚀 Debug Demo App Started       │
│                                 │ │                                 │
│ [DEBUG] App mounted             │ │ ┌─────────────────────────────┐ │
│ [INFO] Layout analysis #1      │ │ │ Textual Debug Demo          │ │
│ [DEBUG] Widget tree logged     │ │ ├─────────────────────────────┤ │
│ [WARN] Overflow detected       │ │ │ Left Panel    │Scroll│Right │ │
│ [INFO] 27 widgets found        │ │ │ [Test Btn 1]  │ Item │Panel │ │
│ [DEBUG] Screen: 120x30         │ │ │ [Test Btn 2]  │ Item │[RED] │ │
│                                 │ │ │               │ Item │WIDE  │ │
│ 🎮 User pressed 'd'            │ │ │               │ Item │WIDGET│ │
│ [INFO] Debug mode ON           │ │ │               │ ...  │      │ │
│ [DEBUG] CSS borders added      │ │ ├─────────────────────────────┤ │
│                                 │ │ │ d=debug l=layout n=notify   │ │
│ 🎮 User pressed 'l'            │ │ └─────────────────────────────┘ │
│ [INFO] Layout analysis #2      │ │                                 │
│ [DEBUG] Widget hierarchy:       │ │ 🔔 Debug mode ON               │
│   Screen [120x30]              │ │                                 │
│   ├─Header [120x1] DOCKED      │ │                                 │
│   ├─Horizontal [120x27]        │ │                                 │
│   │ ├─Vertical [40x27]         │ │                                 │
│   │ ├─VerticalScroll [40x27]   │ │                                 │
│   │ └─Vertical [40x27]         │ │                                 │
│   └─Footer [120x1] DOCKED      │ │                                 │
│ [WARN] problem-widget: 240>120 │ │                                 │
│                                 │ │                                 │
└─────────────────────────────────┘ └─────────────────────────────────┘
```

## 🎨 Debug Mode Visual Changes

### Before Debug Mode (Press 'd'):
```
┌─────────────────────────────────┐
│ Textual Debug Demo              │
├─────────────────────────────────┤
│ Left Panel    │Scroll  │Right   │
│ [Test Btn 1]  │ Item 1 │Panel   │
│ [Test Btn 2]  │ Item 2 │[WIDE]  │
│               │ Item 3 │WIDGET  │
│               │ ...    │        │
├─────────────────────────────────┤
│ d=debug l=layout n=notify       │
└─────────────────────────────────┘
```

### After Debug Mode (Press 'd'):
```
┌─────────────────────────────────┐
│ Textual Debug Demo              │
├─────────────────────────────────┤
│╔Left Panel════╗╔Scroll══╗Right  │
│║ [Test Btn 1] ║║ Item 1  ║Panel  │
│║ [Test Btn 2] ║║ Item 2  ║[RED]  │
│╚══════════════╝║ Item 3  ║WIDE   │
│                ║ ...     ║WIDGET │
│                ╚═════════╝       │
├─────────────────────────────────┤
│ d=debug l=layout n=notify       │
└─────────────────────────────────┘
     BLUE BORDERS    GREEN BORDER
    (containers)     (scrollable)
```

## 📊 Layout Analysis Output (Press 'l'):

```
Console Output:
═══════════════
📊 Layout Analysis #2
🖥️  Screen size: Size(width=120, height=30)

🌳 Widget Tree:
  Screen [120x30] (layout=vertical, overflow_y=auto)
  ├─ Header #header [120x1] (dock=top)
  ├─ Horizontal [120x27] (layout=horizontal)
  │  ├─ Vertical [40x27] (layout=vertical)
  │  │  ├─ Static #left-panel [40x3]
  │  │  ├─ Button #btn1 [40x3]
  │  │  └─ Button #btn2 [40x3]
  │  ├─ VerticalScroll [40x27] (overflow_y=auto)
  │  │  ├─ Static #scroll-area [40x3]
  │  │  ├─ Static .scroll-item-0 [40x1]
  │  │  └─ ... [18 more items]
  │  └─ Vertical [40x27] (layout=vertical)
  │     ├─ Static #right-panel [40x3]
  │     └─ Static .problem-widget [240x3] ⚠️  OVERFLOW!
  └─ Footer #footer [120x1] (dock=bottom)

🚨 Layout Issues Found:
   ⚠️  Static width exceeds screen (problem-widget: 240 > 120)
   ⚠️  Overflow detected in right panel container

✅ Layout analysis completed
```

## 🔔 Notification System (Press 'n'):

```
App Display:                    Console Output:
═══════════                    ══════════════
┌─────────────────────┐       🔔 Test notification at 13:47:23
│🔔 Debug Notification│       [INFO] Notification sent
│  Test notification  │       [DEBUG] Severity: information
│  at 13:47:23        │       
└─────────────────────┘       🔔 Debug Warning
                              [WARN] Warning notification sent
┌─────────────────────┐       [DEBUG] Severity: warning
│⚠️  Debug Warning    │       
│  This is a warning  │       🔔 Debug Error
└─────────────────────┘       [ERROR] Error notification sent
                              [DEBUG] Severity: error
┌─────────────────────┐       
│❌ Debug Error       │       
│  This is an error   │       
└─────────────────────┘       
```

## 📸 Screenshot Capture (Press 's'):

```
Console Output:
═══════════════
📸 Screenshot triggered (screenpipe integration)
📸 Screenshot name: textual_debug_20250918_134723

📊 App state at screenshot:
   Debug mode: True
   Screen size: Size(width=120, height=30)
   Active widgets: 27
   Layout issues: 1 (overflow in problem-widget)
   Performance: 500 renders/sec

🔔 Screenshot saved with metadata correlation
```

## 📏 Responsive Testing (Press 'r'):

```
Console Output:
═══════════════
📏 Resize test initiated
📐 Current screen size: Size(width=120, height=30)

🔍 Simulating resize to 80x24
   ⚠️  Issues at 80x24: 
   - Static too wide (problem-widget: 240 > 80)
   - Horizontal container cramped
   - Scroll area reduced

🔍 Simulating resize to 120x30
   ✅ No critical issues at 120x30
   - Current optimal size
   - All containers fit properly

🔍 Simulating resize to 160x40
   ⚠️  Issues at 160x40:
   - Static still too wide (problem-widget: 240 > 160)
   - Wasted space in containers
   - Could benefit from responsive layout

📊 RESPONSIVE ANALYSIS:
   Best size: 120x30 (current)
   Problem: Fixed 200% width widget
   Recommendation: Use relative units or max-width
```

## 🎮 Interactive Button Testing:

```
User clicks [Test Btn 1]:

App Display:                    Console Output:
═══════════                    ══════════════
┌─────────────────────┐       🔘 Button pressed: btn1
│🔔 Interaction       │       [DEBUG] Screen size: Size(width=120, height=30)
│  Button btn1 pressed│       [DEBUG] Button size: Size(width=40, height=3)
└─────────────────────┘       [DEBUG] Debug mode: True
                              [DEBUG] Click coordinates: (20, 15)
                              [INFO] Interaction logged successfully
```

## 📊 Final Performance Report:

```
🧹 DEBUG SESSION SUMMARY
========================
Duration: 5 minutes 23 seconds
Interactions tested: 6 (d, l, n, s, r, btn1)
Layout analyses: 2
Screenshots: 1
Issues identified: 2
  1. problem-widget overflow (240px > 120px screen)
  2. Non-responsive fixed width layout

Performance Metrics:
  - Render time: 0.002s average
  - Widget count: 27
  - FPS equivalent: 500 renders/sec
  - Memory efficient: Good
  - Layout complexity: Medium

Layout Health Score: 7/10
  ✅ Proper container hierarchy
  ✅ Correct scroll configuration  
  ✅ Responsive horizontal layout
  ✅ Good performance metrics
  ⚠️  One overflow issue
  ⚠️  Fixed width responsiveness
  ⚠️  Missing breakpoint handling

📁 Debug Artifacts Generated:
   - layout_state_1726634823.json (app state snapshot)
   - debug_layout.tcss (temporary debug CSS)
   - debug_helpers.py (analysis functions)
   - screenshot_debug_20250918.png (visual state)
   - performance_metrics.json (timing data)

🎯 ACTIONABLE INSIGHTS:
======================
1. Fix .problem-widget: Change width from 200% to 100% or max-width
2. Add responsive breakpoints for better mobile/desktop support  
3. Consider horizontal scrolling for wide content overflow
4. Implement automated visual regression tests
5. Add performance monitoring alerts for render time spikes

🚀 Workflow Success Rate: 100%
   All debug features worked as expected
   Layout issues successfully identified
   Performance metrics within acceptable ranges
   Visual debugging provided clear insights
```

## 🔧 Behind the Scenes: What Makes This Work

```
Automated Workflow Components:
═══════════════════════════════

1. Service Orchestration:
   ┌─textual console──┐    ┌─textual serve─────┐    ┌─screenpipe────┐
   │ Port: 7342       │◄──►│ Port: 8000        │◄──►│ Visual capture│
   │ Debug logging    │    │ Web inspection    │    │ Screenshots   │
   │ Real-time output │    │ Live CSS editing  │    │ State tracking│
   └──────────────────┘    └───────────────────┘    └───────────────┘
                                    ▲
                                    │
                           ┌─Demo App──────────┐
                           │ Interactive debug │
                           │ Layout analysis   │
                           │ Performance mon.  │
                           │ Issue detection   │
                           └───────────────────┘

2. Debug Data Flow:
   User Input ──► App Action ──► Log Output ──► Console Display
       │               │              │              │
       │               ▼              ▼              ▼
   Keybinding ──► Debug Function ──► Metrics ──► Screenshot
       │               │              │              │
       ▼               ▼              ▼              ▼
   Screenshot ──► State Capture ──► Analysis ──► Report

3. Integrated Analysis:
   ┌─Visual State─┐    ┌─App Metrics─┐    ┌─Performance─┐
   │ Screenshots  │    │ Widget tree │    │ Render time │
   │ Layout view  │◄──►│ Size info   │◄──►│ Memory use  │
   │ Debug borders│    │ Style data  │    │ FPS equiv   │
   └──────────────┘    └─────────────┘    └─────────────┘
           │                    │                    │
           └────────────────────▼────────────────────┘
                         Comprehensive Report
```

This demo showcases how the automated Textual debugging workflow transforms the development experience from manual, fragmented debugging into a comprehensive, integrated system that provides real-time insights, visual feedback, and actionable recommendations for layout issues.
