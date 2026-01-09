"""
Main command for PRT CLI.

This module contains the main entry point command that handles application startup,
mode selection (TUI vs CLI vs Chat), and configuration management.
"""

import typer
from rich.console import Console
from rich.prompt import Confirm

from ...api import PRTAPI
from ..bootstrap.launcher import _launch_tui_with_fallback
from ..bootstrap.launcher import run_interactive_cli
from ..bootstrap.setup import check_setup_status
from ..bootstrap.setup import run_setup_wizard
from ..bootstrap.setup import setup_debug_mode

# print_custom_help removed - using Typer's built-in help
from ..services.llm import start_llm_chat

console = Console()


def main_command(
    ctx: typer.Context,
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Run with sample data (safe, isolated database)"
    ),
    regenerate_fixtures: bool = typer.Option(
        False,
        "--regenerate-fixtures",
        help="Reset sample data (use with --debug)",
    ),
    setup: bool = typer.Option(
        False, "--setup", help="First-time setup: import contacts or try demo data"
    ),
    cli: bool = typer.Option(False, "--cli", help="Use command-line interface instead of TUI"),
    classic: bool = typer.Option(
        False, "--classic", help="Force classic CLI mode (disable TUI attempt)"
    ),
    tui: bool = typer.Option(True, "--tui", help="Use TUI interface (default)"),
    prt_debug_info: bool = typer.Option(
        False, "--prt-debug-info", help="Display system diagnostic information and exit"
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Choose AI model (e.g., 'gpt-oss-20b', 'mistral-7b-instruct'). Use 'list-models' to see options. Put this flag BEFORE --chat.",
    ),
    chat: str | None = typer.Option(
        None,
        "--chat",
        help='Start AI chat mode. Provide query text or use --chat="" for interactive mode. Use AFTER --model flag.',
    ),
    # help_flag removed - Typer handles --help automatically
):
    """
    Personal Relationship Toolkit (PRT)

    A privacy-first contact management system with AI-powered search.
    All data stored locally on your machine, no cloud sync.

    Default behavior: Launches TUI (Text User Interface)
    First time? Run with --setup to import contacts or --debug to try sample data.
    """
    # Custom help is now handled by Typer's built-in --help

    # Handle debug info flag
    if prt_debug_info:
        from .debug import prt_debug_info_command

        prt_debug_info_command()
        return

    # Handle classic flag - force CLI mode
    if classic:
        cli = True
        tui = False

    # Store LLM settings in context for subcommands
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["model"] = model

    # Handle chat mode
    if chat is not None:
        # Handle special case: --chat --
        # This means open chat interface without an initial prompt
        chat_prompt = None if chat == "--" else chat

        # If both --chat and --tui are specified, launch TUI with chat screen
        if tui and not cli:
            _launch_tui_with_fallback(
                debug=debug,
                regenerate_fixtures=regenerate_fixtures,
                force_setup=setup,
                model=model,
                initial_screen="chat",
            )
            return

        # Otherwise, start standalone chat mode
        # Handle debug mode
        if debug:
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
                    console.print("Setup is required to use PRT chat. Exiting.", style="red")
                    raise typer.Exit(1) from None
            else:
                config = status["config"]

        # Create API instance
        try:
            api = PRTAPI(config)
        except Exception as e:
            console.print(f"Failed to initialize API: {e}", style="bold red")
            raise typer.Exit(1) from None

        # Create LLM instance using factory
        console.print("Starting LLM chat mode...", style="blue")
        try:
            from prt_src.llm_factory import create_llm

            llm = create_llm(api=api, model=model)

            # Display model info
            if model:
                console.print(f"Using model: {model}", style="cyan")
            else:
                console.print("Using default model from config", style="cyan")

            # Start interactive chat with initial prompt if provided
            start_llm_chat(llm, api, chat_prompt)
        except Exception as e:
            console.print(f"Error starting chat mode: {e}", style="red")
            console.print("\n💡 Troubleshooting:", style="bold blue")
            console.print(
                "   • Check available models: python -m prt_src.cli list-models", style="dim"
            )
            console.print("   • Use supported model: --model gpt-oss-20b", style="dim")
            console.print("   • Ensure Ollama is running: brew services start ollama", style="dim")
            console.print("   • Install a model: ollama pull gpt-oss:20b", style="dim")
            raise typer.Exit(1) from None
        # Exit after chat session ends
        raise typer.Exit(0)

    if ctx.invoked_subcommand is None:
        if cli:
            run_interactive_cli(
                debug=debug,
                regenerate_fixtures=regenerate_fixtures,
                model=model,
            )
        else:
            # Launch TUI by default or when explicitly requested
            _launch_tui_with_fallback(
                debug=debug,
                regenerate_fixtures=regenerate_fixtures,
                force_setup=setup,
                model=model,
            )
