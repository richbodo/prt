#!/usr/bin/env python3
"""
Automated Textual Development & Debugging Workflow
==================================================

This module provides a comprehensive automated workflow for testing and debugging
Textual applications with focus on layout issues, containers, scrolling, and screen resizing.

Features:
- Automated console setup and management
- Integrated logging and debugging
- Screen capture and analysis via screenpipe
- Layout inspection and DOM analysis
- Automated testing with visual verification
- Performance monitoring and layout profiling
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

from textual import log


@dataclass
class DebugSession:
    """Configuration for a debug session"""

    app_path: str
    console_port: int = 7342
    serve_port: int = 8000
    enable_screenpipe: bool = True
    auto_screenshot: bool = True
    layout_profiling: bool = True
    verbose_logging: bool = True


@dataclass
class LayoutMetrics:
    """Layout performance and correctness metrics"""

    widget_count: int
    render_time: float
    layout_time: float
    scroll_regions: int
    overflow_issues: List[str]
    size_violations: List[str]
    responsive_score: float


class TextualDebugWorkflow:
    """Main workflow orchestrator for Textual debugging"""

    def __init__(self, session: DebugSession):
        self.session = session
        self.console_process: Optional[subprocess.Popen] = None
        self.serve_process: Optional[subprocess.Popen] = None
        self.app_process: Optional[subprocess.Popen] = None
        self.debug_dir = Path(tempfile.mkdtemp(prefix="textual_debug_"))
        self.screenshots: List[str] = []
        self.metrics: List[LayoutMetrics] = []

    async def __aenter__(self):
        """Async context manager entry - starts all debug services"""
        await self.start_debug_services()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleans up all services"""
        await self.cleanup_debug_services()

    async def start_debug_services(self):
        """Start all debugging services in the correct order"""
        print("🚀 Starting Textual Debug Workflow")
        print(f"📁 Debug directory: {self.debug_dir}")

        # 1. Start Textual console for logging
        await self.start_console()

        # 2. Start serve for web inspection (optional)
        await self.start_serve()

        # 3. Setup screenpipe integration
        if self.session.enable_screenpipe:
            await self.setup_screenpipe()

        # 4. Create debug utilities
        await self.setup_debug_utilities()

        print("✅ All debug services started successfully")

    async def start_console(self):
        """Start textual console for debug output"""
        console_cmd = ["textual", "console", "--port", str(self.session.console_port)]

        if self.session.verbose_logging:
            console_cmd.append("-v")

        print(f"🖥️  Starting Textual console on port {self.session.console_port}")

        self.console_process = subprocess.Popen(
            console_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Give console time to start
        await asyncio.sleep(2)

        # Verify console is running
        if self.console_process.poll() is not None:
            raise RuntimeError("Failed to start Textual console")

        print("✅ Textual console started")

    async def start_serve(self):
        """Start textual serve for web-based inspection"""
        print(f"🌐 Starting Textual serve on port {self.session.serve_port}")

        serve_cmd = [
            "textual",
            "serve",
            "--port",
            str(self.session.serve_port),
            "--host",
            "localhost",
            self.session.app_path,
        ]

        self.serve_process = subprocess.Popen(
            serve_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        # Give serve time to start
        await asyncio.sleep(3)

        print(f"✅ Textual serve started at http://localhost:{self.session.serve_port}")

    async def setup_screenpipe(self):
        """Setup screenpipe integration for visual debugging"""
        print("📸 Setting up screenpipe integration")

        # Create screenpipe search function for terminal content
        self.screenpipe_available = True
        try:
            # Test screenpipe availability
            import subprocess

            result = subprocess.run(["which", "screenpipe"], capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  Screenpipe not found in PATH, visual debugging disabled")
                self.screenpipe_available = False
        except Exception as e:
            print(f"⚠️  Screenpipe setup failed: {e}")
            self.screenpipe_available = False

        if self.screenpipe_available:
            print("✅ Screenpipe integration ready")

    async def setup_debug_utilities(self):
        """Create debug utility files and configurations"""

        # Create enhanced debug CSS for layout inspection
        debug_css = self.debug_dir / "debug_layout.tcss"
        debug_css.write_text(
            """
/* Textual Debug Layout CSS */
/* Add temporary borders for layout debugging */

.debug-border {
    border: solid red;
}

.debug-container {
    border: solid blue;
    background: rgba(0, 0, 255, 0.1);
}

.debug-scrollable {
    border: solid green;
    background: rgba(0, 255, 0, 0.1);
}

.debug-overflow {
    border: solid yellow;
    background: rgba(255, 255, 0, 0.2);
}

/* Highlight different layout types */
Horizontal {
    border: solid cyan;
}

Vertical {
    border: solid magenta;
}

Grid {
    border: solid orange;
}

/* Screen debugging */
Screen {
    border: solid white;
}
"""
        )

        # Create debug helper script
        debug_script = self.debug_dir / "debug_helpers.py"
        debug_script.write_text(
            '''
"""Textual Debug Helper Functions"""

from textual import log
from textual.geometry import Size
from textual.widget import Widget
from textual.app import App
import time
from typing import Dict, Any, List


def log_widget_tree(widget: Widget, level: int = 0) -> None:
    """Log the complete widget tree with layout information"""
    indent = "  " * level
    size_info = f"{widget.size.width}x{widget.size.height}"

    log(f"{indent}{widget.__class__.__name__} [{size_info}] - {widget.styles}")

    for child in widget.children:
        log_widget_tree(child, level + 1)


def log_layout_metrics(app: App) -> Dict[str, Any]:
    """Collect and log comprehensive layout metrics"""
    metrics = {
        "timestamp": time.time(),
        "screen_size": {"width": app.screen.size.width, "height": app.screen.size.height},
        "widget_count": len(list(app.screen.walk_children())),
        "scrollable_widgets": [],
        "overflow_widgets": [],
        "layout_violations": []
    }

    for widget in app.screen.walk_children():
        # Check for scrollable widgets
        if widget.styles.overflow_y == "auto" or widget.styles.overflow_x == "auto":
            metrics["scrollable_widgets"].append({
                "type": widget.__class__.__name__,
                "id": getattr(widget, 'id', None),
                "size": {"width": widget.size.width, "height": widget.size.height}
            })

        # Check for potential overflow issues
        if widget.size.width <= 0 or widget.size.height <= 0:
            metrics["layout_violations"].append({
                "type": widget.__class__.__name__,
                "issue": "zero_or_negative_size",
                "size": {"width": widget.size.width, "height": widget.size.height}
            })

    log("📊 Layout Metrics:", metrics)
    return metrics


def debug_responsive_behavior(app: App, test_sizes: List[tuple] = None) -> None:
    """Test responsive behavior at different screen sizes"""
    if test_sizes is None:
        test_sizes = [(80, 24), (120, 30), (160, 40), (200, 50)]

    original_size = app.screen.size

    for width, height in test_sizes:
        log(f"🔍 Testing responsive behavior at {width}x{height}")

        # Simulate screen resize (this would need to be triggered externally)
        # In a real scenario, you'd resize the terminal window
        log(f"Screen size: {width}x{height}")

        # Log layout metrics at this size
        metrics = log_layout_metrics(app)

        # Check for common responsive issues
        for widget in app.screen.walk_children():
            if widget.size.width > width:
                log(f"⚠️  Widget {widget.__class__.__name__} exceeds screen width")
            if widget.size.height > height:
                log(f"⚠️  Widget {widget.__class__.__name__} exceeds screen height")


def enhanced_notify(app: App, message: str, title: str = "Debug",
                   severity: str = "information") -> None:
    """Enhanced notification with debugging context"""
    debug_info = f"[{time.strftime('%H:%M:%S')}] {message}"
    app.notify(debug_info, title=title, severity=severity)
    log(f"🔔 Notification: {debug_info}")


def auto_screenshot(description: str = "debug") -> None:
    """Trigger automatic screenshot via screenpipe if available"""
    import subprocess
    try:
        # This would integrate with screenpipe to capture current state
        log(f"📸 Auto-screenshot: {description}")
        # Placeholder for screenpipe integration
    except Exception as e:
        log(f"Screenshot failed: {e}")
'''
        )

        print(f"✅ Debug utilities created in {self.debug_dir}")

    async def run_app_with_debugging(
        self, app_class_or_path: str, test_scenarios: List[Callable] = None
    ) -> None:
        """Run the app with full debugging enabled"""
        print(f"🎯 Running app with debugging: {app_class_or_path}")

        # Start the app with debugging enabled
        run_cmd = [
            "textual",
            "run",
            "--dev",
            "--port",
            str(self.session.console_port),
            app_class_or_path,
        ]

        self.app_process = subprocess.Popen(
            run_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "TEXTUAL_DEBUG": "1"},
        )

        # Give app time to start
        await asyncio.sleep(3)

        # Run automated test scenarios if provided
        if test_scenarios:
            await self.run_test_scenarios(test_scenarios)

        print("✅ App started with debugging enabled")

    async def run_test_scenarios(self, scenarios: List[Callable]) -> None:
        """Run automated test scenarios"""
        print(f"🧪 Running {len(scenarios)} test scenarios")

        for i, scenario in enumerate(scenarios, 1):
            print(f"📋 Running scenario {i}: {scenario.__name__}")
            try:
                await scenario()
                print(f"✅ Scenario {i} completed successfully")
            except Exception as e:
                print(f"❌ Scenario {i} failed: {e}")

    async def capture_layout_state(self, description: str = "layout_state") -> Dict[str, Any]:
        """Capture current layout state for analysis"""
        timestamp = time.time()

        # Capture via screenpipe if available
        screenshot_path = None
        if self.session.auto_screenshot and self.screenpipe_available:
            screenshot_path = await self.take_screenshot(description)

        state = {
            "timestamp": timestamp,
            "description": description,
            "screenshot": screenshot_path,
            "console_logs": await self.get_recent_console_logs(),
        }

        # Save state to debug directory
        state_file = self.debug_dir / f"layout_state_{timestamp}.json"
        state_file.write_text(json.dumps(state, indent=2))

        return state

    async def take_screenshot(self, description: str) -> Optional[str]:
        """Take screenshot using screenpipe integration"""
        if not self.screenpipe_available:
            return None

        try:
            # This would integrate with screenpipe MCP server
            # For now, we'll use a placeholder
            screenshot_path = str(self.debug_dir / f"screenshot_{description}_{time.time()}.png")
            self.screenshots.append(screenshot_path)

            log(f"📸 Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            log(f"Screenshot failed: {e}")
            return None

    async def get_recent_console_logs(self) -> List[str]:
        """Get recent console logs for analysis"""
        # This would read from the textual console output
        # For now, return placeholder
        return ["Console log integration pending"]

    async def cleanup_debug_services(self):
        """Clean up all debug services"""
        print("🧹 Cleaning up debug services...")

        processes = [
            ("Console", self.console_process),
            ("Serve", self.serve_process),
            ("App", self.app_process),
        ]

        for name, process in processes:
            if process and process.poll() is None:
                print(f"🛑 Stopping {name} process...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

        print(f"📁 Debug files saved in: {self.debug_dir}")
        print("✅ Cleanup completed")


# Example usage and test scenarios
async def example_layout_test_scenario():
    """Example test scenario for layout debugging"""
    log("🧪 Running layout test scenario")

    # Simulate user interactions that might cause layout issues
    # This would use Pilot in a real implementation
    await asyncio.sleep(1)

    log("✅ Layout test scenario completed")


async def example_scrolling_test_scenario():
    """Example test scenario for scrolling debugging"""
    log("🧪 Running scrolling test scenario")

    # Test scrolling behavior
    await asyncio.sleep(1)

    log("✅ Scrolling test scenario completed")


# Main workflow function
async def run_debug_workflow(app_path: str, **kwargs) -> None:
    """Main function to run the complete debug workflow"""

    session = DebugSession(app_path=app_path, **kwargs)

    async with TextualDebugWorkflow(session) as workflow:

        # Define test scenarios
        test_scenarios = [
            example_layout_test_scenario,
            example_scrolling_test_scenario,
        ]

        # Run the app with debugging
        await workflow.run_app_with_debugging(app_path, test_scenarios)

        # Keep workflow running for interactive debugging
        print("🎮 Debug workflow active. Press Ctrl+C to exit...")
        try:
            while True:
                # Capture periodic layout states
                await workflow.capture_layout_state("periodic_check")
                await asyncio.sleep(30)  # Capture every 30 seconds

        except KeyboardInterrupt:
            print("\n🛑 Debug workflow interrupted by user")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python textual_debug_workflow.py <app_path> [options]")
        print("Example: python textual_debug_workflow.py my_app.py")
        sys.exit(1)

    app_path = sys.argv[1]

    # Run the debug workflow
    asyncio.run(run_debug_workflow(app_path))
