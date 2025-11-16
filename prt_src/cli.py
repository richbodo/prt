"""
PRT CLI - Modular Command Line Interface

This module provides a thin compatibility layer that imports the modular CLI structure.
The actual CLI implementation has been refactored into multiple specialized modules.

Deprecation Notice:
This file serves as a compatibility shim. The modular structure is in:
- prt_src/cli_modules/app.py - Main Typer application
- prt_src/cli_modules/commands/ - Command implementations
- prt_src/cli_modules/handlers/ - Domain handlers
- prt_src/cli_modules/services/ - Business services
- prt_src/cli_modules/ui/ - UI utilities
- prt_src/cli_modules/bootstrap/ - Application bootstrap

For new development, use the modular structure directly.
"""

# Import the modular CLI app
# Import Rich console for test compatibility
from rich.console import Console

from .cli_modules.app import app
from .cli_modules.bootstrap.launcher import run_interactive_cli

# Preserve the main menu function for backward compatibility
from .cli_modules.handlers.menu import show_main_menu

# Import missing functions for backward compatibility
from .cli_modules.services.export import export_search_results

console = Console()


# Create a local wrapper for _launch_tui_with_fallback that uses local imports
# This enables proper mocking in tests
def _launch_tui_with_fallback(
    debug: bool = False,
    regenerate_fixtures: bool = False,
    force_setup: bool = False,
    model: str = None,
    initial_screen: str = None,
) -> None:
    """Launch TUI with fallback to classic CLI on failure."""
    try:
        from prt_src.tui.app import PRTApp

        if debug:
            from .cli_modules.bootstrap.setup import setup_debug_mode

            console.print(
                "🐛 [bold cyan]DEBUG MODE ENABLED[/bold cyan] - Using fixture data", style="cyan"
            )
            config = setup_debug_mode(regenerate=regenerate_fixtures)
            app = PRTApp(
                config=config,
                debug=True,
                force_setup=force_setup,
                model=model,
                initial_screen=initial_screen,
            )
        else:
            app = PRTApp(force_setup=force_setup, model=model, initial_screen=initial_screen)

        app.run()
    except Exception as e:
        console.print(f"Failed to launch TUI: {e}", style="red")
        console.print("Falling back to classic CLI...", style="yellow")
        run_interactive_cli(
            debug=debug,
            regenerate_fixtures=regenerate_fixtures,
            model=model,
        )


# Export the app for __main__.py
__all__ = [
    "app",
    "show_main_menu",
    "export_search_results",
    "_launch_tui_with_fallback",
    "run_interactive_cli",
    "console",
]


if __name__ == "__main__":
    app()
