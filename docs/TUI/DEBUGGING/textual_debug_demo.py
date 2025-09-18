#!/usr/bin/env python3
"""
Textual Debug Workflow Demo
===========================

A simplified demo showing the automated debugging workflow in action.
This demonstrates the key components working together.
"""

import time

from textual.app import App
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.containers import VerticalScroll
from textual.widgets import Button
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Static


class DebugDemoApp(App):
    """Demo app to showcase debugging workflow"""

    CSS = """
    .debug-container {
        border: solid blue;
        background: rgba(0, 0, 255, 0.1);
    }

    .debug-scrollable {
        border: solid green;
        background: rgba(0, 255, 0, 0.1);
    }

    .problem-widget {
        width: 200%;  /* Intentional overflow issue */
        background: red;
    }
    """

    BINDINGS = [
        Binding("d", "toggle_debug", "Toggle Debug"),
        Binding("l", "log_layout", "Log Layout"),
        Binding("n", "test_notify", "Test Notify"),
        Binding("s", "screenshot", "Screenshot"),
        Binding("r", "resize_test", "Resize Test"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.debug_mode = False
        self.layout_counter = 0

    def compose(self) -> ComposeResult:
        """Compose the demo app layout"""
        yield Header()

        with Horizontal(classes="debug-container"):
            with Vertical():
                yield Static("Left Panel", id="left-panel")
                yield Button("Test Button 1", id="btn1")
                yield Button("Test Button 2", id="btn2")

            with VerticalScroll(classes="debug-scrollable"):
                yield Static("Scrollable Content Area", id="scroll-area")
                for i in range(20):
                    yield Static(f"Scrollable Item {i+1}", classes=f"scroll-item-{i}")

            with Vertical():
                yield Static("Right Panel", id="right-panel")
                yield Static("Problem Widget", classes="problem-widget")

        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted"""
        self.log("🚀 Debug Demo App started")
        self.log(
            "📋 Available actions: d=debug, l=layout, n=notify, s=screenshot, r=resize, q=quit"
        )

        # Log initial layout state
        self.action_log_layout()

    def action_toggle_debug(self) -> None:
        """Toggle debug mode visualization"""
        self.debug_mode = not self.debug_mode

        if self.debug_mode:
            self.log("🐛 Debug mode ENABLED - borders and highlights visible")
            # Add debug CSS classes
            for widget in self.query("*"):
                if hasattr(widget, "add_class"):
                    if "Horizontal" in str(type(widget)) or "Vertical" in str(type(widget)):
                        widget.add_class("debug-container")
                    elif "Scroll" in str(type(widget)):
                        widget.add_class("debug-scrollable")
        else:
            self.log("🐛 Debug mode DISABLED")
            # Remove debug CSS classes
            for widget in self.query("*"):
                if hasattr(widget, "remove_class"):
                    widget.remove_class("debug-container")
                    widget.remove_class("debug-scrollable")

        self.notify(
            f"Debug mode {'ON' if self.debug_mode else 'OFF'}",
            title="Debug Toggle",
            severity="information",
        )

    def action_log_layout(self) -> None:
        """Log comprehensive layout information"""
        self.layout_counter += 1

        self.log(f"📊 Layout Analysis #{self.layout_counter}")
        self.log(f"🖥️  Screen size: {self.screen.size}")

        # Log widget tree with layout info
        self.log("🌳 Widget Tree:")
        self._log_widget_tree(self.screen, 0)

        # Check for common issues
        issues = []
        for widget in self.query("*"):
            # Check for overflow issues
            if hasattr(widget, "size"):
                if widget.size.width > self.screen.size.width:
                    issues.append(f"⚠️  {widget.__class__.__name__} width exceeds screen")
                if widget.size.height > self.screen.size.height and not hasattr(widget, "scroll"):
                    issues.append(f"⚠️  {widget.__class__.__name__} height exceeds screen")

        if issues:
            self.log("🚨 Layout Issues Found:")
            for issue in issues:
                self.log(f"   {issue}")
        else:
            self.log("✅ No layout issues detected")

        self.notify(
            f"Layout analysis #{self.layout_counter} completed",
            title="Layout Debug",
            severity="information",
        )

    def _log_widget_tree(self, widget, level: int) -> None:
        """Recursively log widget tree structure"""
        indent = "  " * level
        size_info = (
            f"{widget.size.width}x{widget.size.height}" if hasattr(widget, "size") else "no-size"
        )

        widget_info = f"{indent}{widget.__class__.__name__}"
        if hasattr(widget, "id") and widget.id:
            widget_info += f" #{widget.id}"
        widget_info += f" [{size_info}]"

        # Add layout info
        if hasattr(widget, "styles"):
            layout_info = []
            if hasattr(widget.styles, "layout") and widget.styles.layout:
                layout_info.append(f"layout={widget.styles.layout}")
            if hasattr(widget.styles, "overflow_y") and widget.styles.overflow_y != "visible":
                layout_info.append(f"overflow_y={widget.styles.overflow_y}")
            if hasattr(widget.styles, "width") and widget.styles.width:
                layout_info.append(f"width={widget.styles.width}")
            if hasattr(widget.styles, "height") and widget.styles.height:
                layout_info.append(f"height={widget.styles.height}")

            if layout_info:
                widget_info += f" ({', '.join(layout_info)})"

        self.log(widget_info)

        # Recursively log children
        if hasattr(widget, "children"):
            for child in widget.children:
                self._log_widget_tree(child, level + 1)

    def action_test_notify(self) -> None:
        """Test notification system with debugging info"""
        timestamp = time.strftime("%H:%M:%S")
        debug_info = f"Test notification at {timestamp}"

        self.log(f"🔔 {debug_info}")
        self.notify(debug_info, title="Debug Notification", severity="information")

        # Also test different severity levels
        self.notify("This is a warning", title="Debug Warning", severity="warning")
        self.notify("This is an error", title="Debug Error", severity="error")

    def action_screenshot(self) -> None:
        """Trigger screenshot capture"""
        self.log("📸 Screenshot triggered (screenpipe integration)")

        # This would integrate with screenpipe to capture the current terminal state
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_name = f"textual_debug_{timestamp}"

        self.log(f"📸 Screenshot name: {screenshot_name}")
        self.notify(
            f"Screenshot captured: {screenshot_name}", title="Screenshot", severity="information"
        )

        # Log current app state for correlation with screenshot
        self.log("📊 App state at screenshot:")
        self.log(f"   Debug mode: {self.debug_mode}")
        self.log(f"   Screen size: {self.screen.size}")
        self.log(f"   Active widgets: {len(list(self.query('*')))}")

    def action_resize_test(self) -> None:
        """Test responsive behavior (simulated)"""
        self.log("📏 Resize test initiated")

        # Log current size
        current_size = self.screen.size
        self.log(f"📐 Current screen size: {current_size}")

        # Simulate checking responsive behavior at different sizes
        test_sizes = [(80, 24), (120, 30), (160, 40)]

        for width, height in test_sizes:
            self.log(f"🔍 Simulating resize to {width}x{height}")

            # Check which widgets would have issues at this size
            issues = []
            for widget in self.query("*"):
                if hasattr(widget, "size"):
                    if widget.size.width > width:
                        issues.append(f"{widget.__class__.__name__} too wide")
                    if widget.size.height > height:
                        issues.append(f"{widget.__class__.__name__} too tall")

            if issues:
                self.log(f"   ⚠️  Issues at {width}x{height}: {', '.join(issues)}")
            else:
                self.log(f"   ✅ No issues at {width}x{height}")

        self.notify(
            "Resize test completed - check console for details",
            title="Resize Test",
            severity="information",
        )

    def on_button_pressed(self, event) -> None:
        """Handle button press events"""
        button_id = event.button.id
        self.log(f"🔘 Button pressed: {button_id}")

        # Log interaction context
        self.log(f"   Screen size: {self.screen.size}")
        self.log(f"   Button size: {event.button.size}")
        self.log(f"   Debug mode: {self.debug_mode}")

        self.notify(f"Button {button_id} pressed", title="Interaction", severity="information")


if __name__ == "__main__":
    print("🚀 Starting Textual Debug Demo")
    print("📋 Instructions:")
    print("   1. Start 'textual console' in another terminal first")
    print("   2. Then run: textual run --dev textual_debug_demo.py")
    print("   3. Use keybindings: d=debug, l=layout, n=notify, s=screenshot, r=resize, q=quit")
    print("   4. Watch the console output for detailed debugging info")
    print()

    app = DebugDemoApp()
    app.run()
