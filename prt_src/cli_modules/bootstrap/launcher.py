"""
Application launcher utilities for PRT CLI.

Functions for launching the interactive CLI and TUI with proper fallback handling.
These functions manage the main application startup process.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.prompt import Prompt
from rich.text import Text

from ...api import PRTAPI
from .health import check_database_health
from .setup import check_setup_status
from .setup import run_setup_wizard
from .setup import setup_debug_mode


def run_interactive_cli(
    debug: bool = False,
    regenerate_fixtures: bool = False,
    model: str | None = None,
):
    """Run the main interactive CLI."""
    console = Console()

    if debug:
        console.print(
            "🐛 [bold cyan]DEBUG MODE ENABLED[/bold cyan] - Using fixture data", style="cyan"
        )
        config = setup_debug_mode(regenerate=regenerate_fixtures)
    else:
        # Check setup status
        status = check_setup_status()

        if status["needs_setup"]:
            console.print(f"PRT needs to be set up: {status['reason']}", style="yellow")
            console.print()

            if Confirm.ask("Would you like to run the setup wizard now?"):
                config = run_setup_wizard()
            else:
                console.print("Setup is required to use PRT. Exiting.", style="red")
                raise typer.Exit(1) from None
        else:
            config = status["config"]

    # Create API instance
    try:
        api = PRTAPI(config)
    except Exception as e:
        console.print(f"Failed to initialize API: {e}", style="bold red")
        raise typer.Exit(1) from None

    # Check database health on startup (only in non-debug mode)
    if not debug:
        health = check_database_health(api)
        if not health["healthy"] and health.get("needs_initialization"):
            startup_text = Text()
            startup_text.append("🏗️  Database Initialization Required\n\n", style="bold yellow")
            startup_text.append("Your database needs to be set up with tables.\n", style="yellow")
            startup_text.append("This is normal for first-time use!\n\n", style="yellow")
            startup_text.append("📋 Recommended next steps:\n", style="bold blue")
            startup_text.append("   • Use option 3 to import Google Takeout\n", style="green")
            startup_text.append(
                "   • This will automatically create the required tables\n", style="green"
            )
            startup_text.append("   • Then you can explore all PRT features!\n", style="green")

            console.print(Panel(startup_text, title="Welcome to PRT", border_style="blue"))
            console.print()  # Add some spacing
        elif health["healthy"] and not health["has_data"]:
            startup_text = Text()
            startup_text.append("📭 Database is set up but empty\n\n", style="yellow")
            startup_text.append(
                "Ready to import your contacts! Use option 3 to import Google Takeout.",
                style="green",
            )

            console.print(Panel(startup_text, title="Ready to Import", border_style="green"))
            console.print()

    # Import the modular handlers
    from ..handlers.contacts import handle_contacts_view
    from ..handlers.database import handle_database_menu
    from ..handlers.menu import show_main_menu
    from ..handlers.notes import handle_notes_menu
    from ..handlers.relationships import handle_relationships_menu
    from ..handlers.search import handle_search_menu
    from ..handlers.tags import handle_tags_menu
    from ..services.import_google import handle_import_google_takeout

    # Main interactive loop with new menu structure
    while True:
        try:
            show_main_menu(api)
            choice = Prompt.ask(
                "Select an option",
                choices=["c", "v", "r", "s", "t", "n", "d", "i", "q"],
                default="c",
            )

            if choice == "q":
                console.print("Goodbye!", style="green")
                break
            elif choice == "c":
                try:
                    # Import the old function temporarily until we refactor chat handling
                    from ...llm_ollama import start_ollama_chat

                    start_ollama_chat(api)
                    # Chat mode handles its own flow - no continue prompt needed
                    continue
                except Exception as e:
                    console.print(f"Error starting chat mode: {e}", style="red")
                    console.print(
                        "Make sure Ollama is running and gpt-oss:20b model is available.",
                        style="yellow",
                    )
            elif choice == "v":
                handle_contacts_view(api)
            elif choice == "r":
                handle_relationships_menu(api)
            elif choice == "s":
                handle_search_menu(api)
            elif choice == "t":
                handle_tags_menu(api)
            elif choice == "n":
                handle_notes_menu(api)
            elif choice == "d":
                handle_database_menu(api)
            elif choice == "i":
                handle_import_google_takeout(api, config)

            # Smart continuation - only prompt when needed
            if choice not in ["q", "c"]:
                from ..ui.prompts import smart_continue_prompt

                smart_continue_prompt(choice)

        except KeyboardInterrupt:
            console.print("\nGoodbye!", style="green")
            break


def _launch_tui_with_fallback(
    debug: bool = False,
    regenerate_fixtures: bool = False,
    force_setup: bool = False,
    model: str | None = None,
    initial_screen: str | None = None,
) -> None:
    """Launch TUI with fallback to classic CLI on failure."""
    console = Console()

    try:
        from prt_src.tui.app import PRTApp

        if debug:
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
