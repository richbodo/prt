"""
PRT - Personal Relationship Toolkit CLI

This is the main CLI interface for PRT. It automatically detects if setup is needed
and provides a unified interface for all operations.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from .api import PRTAPI
from .cli_modules.bootstrap.launcher import _launch_tui_with_fallback
from .cli_modules.bootstrap.launcher import run_interactive_cli
from .cli_modules.bootstrap.setup import check_setup_status
from .cli_modules.bootstrap.setup import run_setup_wizard
from .cli_modules.bootstrap.setup import setup_debug_mode
from .cli_modules.help import print_custom_help
from .cli_modules.services.llm import start_llm_chat
from .config import load_config
from .db import create_database

# Encryption imports removed as part of Issue #41

app = typer.Typer(
    help="Personal Relationship Toolkit (PRT) - Privacy-first contact management with AI-powered search",
    add_completion=False,
    no_args_is_help=False,
)
console = Console()

# Required configuration fields
REQUIRED_FIELDS = ["db_username", "db_password", "db_path"]

# Configuration constants for relationship management
DEFAULT_PAGE_SIZE = 20  # Default number of items per page
MAX_DISPLAY_CONTACTS = 30  # Maximum contacts to show without pagination
TABLE_WIDTH_LIMIT = 120  # Maximum table width

# Security constants
MAX_CSV_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
MAX_CSV_IMPORT_ROWS = 10000  # Maximum relationships to import
EXPORT_FILE_PERMISSIONS = 0o600  # rw-------
EXPORT_DIR_PERMISSIONS = 0o750  # rwxr-x---


def show_main_menu(api: PRTAPI):
    """Display the improved main operations menu with safe, visible colors."""
    # Use Rich's table grid for consistent formatting and safe colors
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bright_blue bold", width=4)  # High contrast for shortcuts
    table.add_column(style="default")  # Default terminal color for descriptions

    # Menu items with safe, high-contrast colors
    table.add_row(
        "c.",
        "[bright_green bold]Start Chat[/bright_green bold] - AI-powered chat mode that does anything the cli and tools can do and more",
    )
    table.add_row(
        "v.", "[bright_cyan bold]View Contacts[/bright_cyan bold] - Browse contact information"
    )
    table.add_row(
        "r.",
        "[bright_yellow bold]Manage Relationships[/bright_yellow bold] - View and manage contact relationships",
    )
    table.add_row(
        "s.",
        "[bright_magenta bold]Search[/bright_magenta bold] - Search contacts by contact, tag, or note content - export any results list to a directory",
    )
    table.add_row(
        "t.",
        "[bright_yellow bold]Manage Tags[/bright_yellow bold] - Browse and manage contact tags",
    )
    table.add_row("n.", "[blue bold]Manage Notes[/blue bold] - Browse and manage contact notes")
    table.add_row(
        "d.", "[magenta bold]Manage Database[/magenta bold] - Check database stats and backup"
    )
    table.add_row(
        "i.",
        "[green bold]Import Google Takeout[/green bold] - Import contacts from Google Takeout zip file",
    )
    table.add_row("q.", "[bright_red bold]Exit[/bright_red bold] - Exit the application")

    console.print(
        Panel(
            table,
            title="[bright_blue bold]Personal Relationship Toolkit (PRT)[/bright_blue bold]",
            border_style="bright_blue",
        )
    )


# Helper functions for relationship management

# Advanced Relationship Management Features (Issue #64 Part 3)


def main(
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
    tui: bool = typer.Option(True, "--tui", help="Use TUI interface (default)"),
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
    help_flag: bool = typer.Option(False, "--help", help="Show this message and exit."),
):
    """
    Personal Relationship Toolkit (PRT)

    A privacy-first contact management system with AI-powered search.
    All data stored locally on your machine, no cloud sync.

    Default behavior: Launches TUI (Text User Interface)
    First time? Run with --setup to import contacts or --debug to try sample data.
    """
    # Handle custom help first
    if help_flag:
        print_custom_help()
        raise typer.Exit()

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


@app.command()
def test_db():
    """Test database connection and credentials."""
    try:
        config = load_config()
        if not config:
            console.print("No configuration found. Run 'setup' first.", style="red")
            raise typer.Exit(1) from None

        db_path = Path(config.get("db_path", "prt_data/prt.db"))
        console.print(f"Testing database connection to: {db_path}", style="blue")

        if not db_path.exists():
            console.print("Database file not found.", style="red")
            raise typer.Exit(1) from None

        # Try to connect to database
        db = create_database(db_path)

        if db.is_valid():
            console.print("✓ Database connection successful", style="green")
            console.print(f"  Contacts: {db.count_contacts()}", style="green")
            console.print(f"  Relationships: {db.count_relationships()}", style="green")
        else:
            console.print("✗ Database is corrupted or invalid", style="red")
            raise typer.Exit(1) from None

    except Exception as e:
        console.print(f"✗ Database test failed: {e}", style="red")
        raise typer.Exit(1) from None


@app.command()
def list_models():
    """List available LLM models with support status and hardware requirements."""
    try:
        from prt_src.llm_factory import get_registry
        from prt_src.llm_supported_models import get_hardware_guidance
        from prt_src.llm_supported_models import get_model_support_info
        from prt_src.llm_supported_models import get_recommended_model

        console.print("🔍 Discovering available models...\n", style="bold blue")

        registry = get_registry()

        # Check if Ollama is available
        if not registry.is_available():
            console.print("⚠️  Ollama is not running or not accessible", style="yellow")
            console.print("   Make sure Ollama is running: brew services start ollama", style="dim")
            console.print("   Install Ollama: https://ollama.com/", style="dim")
            raise typer.Exit(1) from None

        # List all models
        models = registry.list_models(force_refresh=True)

        if not models:
            console.print("No models found in Ollama", style="yellow")
            recommended = get_recommended_model()
            console.print(
                f"   Install recommended model: ollama pull {recommended.model_name}", style="dim"
            )
            console.print("   Install any model: ollama pull llama3", style="dim")
            raise typer.Exit(1) from None

        # Create enhanced table with support status and hardware info
        table = Table(title="Available Models", show_header=True)
        table.add_column("Alias", style="cyan", no_wrap=True, width=20)
        table.add_column("Full Name", style="white", width=25)
        table.add_column("Size", style="green", justify="right", width=10)
        table.add_column("Support", style="bright_white", justify="center", width=12)
        table.add_column("Hardware Requirements", style="yellow", width=40)

        # Get default model
        default_model = registry.get_default_model()

        # Sort models: supported first, then by support status, then by name
        def sort_key(model):
            support_info = get_model_support_info(model.name) or get_model_support_info(
                model.friendly_name
            )
            if support_info:
                status_priority = {"official": 0, "experimental": 1, "deprecated": 2}
                return (0, status_priority.get(support_info.support_status, 3), model.name)
            else:
                return (1, 3, model.name)  # Unsupported models last

        sorted_models = sorted(models, key=sort_key)

        # Add rows
        for model in sorted_models:
            # Check support status
            support_info = get_model_support_info(model.name) or get_model_support_info(
                model.friendly_name
            )

            # Format alias with indicators
            alias = model.friendly_name
            if model.name == default_model:
                alias = f"⭐ {alias}"

            # Support status styling
            if support_info:
                if support_info.support_status == "official":
                    support_text = "✅ Official"
                    support_style = "green"
                elif support_info.support_status == "experimental":
                    support_text = "🧪 Experimental"
                    support_style = "yellow"
                elif support_info.support_status == "deprecated":
                    support_text = "⚠️ Deprecated"
                    support_style = "red"
                else:
                    support_text = support_info.support_status.title()
                    support_style = "white"

                # Hardware requirements
                hardware_text = get_hardware_guidance(support_info)
            else:
                support_text = "❓ Unsupported"
                support_style = "dim"
                # Basic hardware info for unsupported models
                model_type = "Local GGUF" if model.is_local_gguf() else "Ollama"
                hardware_text = f"Type: {model_type} | Size: {model.size_human}"

            table.add_row(
                alias,
                model.name,
                model.size_human,
                f"[{support_style}]{support_text}[/]",
                hardware_text,
            )

        console.print(table)
        console.print()

        # Show recommendations and usage
        console.print("🎯 Recommendations:", style="bold blue")

        # Show officially supported models
        official_models = [
            m
            for m in sorted_models
            if (get_model_support_info(m.name) or get_model_support_info(m.friendly_name))
            and (
                get_model_support_info(m.name) or get_model_support_info(m.friendly_name)
            ).support_status
            == "official"
        ]

        if official_models:
            console.print("   ✅ Officially supported (recommended):", style="green")
            for model in official_models[:3]:  # Show top 3
                support_info = get_model_support_info(model.name) or get_model_support_info(
                    model.friendly_name
                )
                console.print(
                    f"      • {support_info.display_name} ({model.friendly_name}) - {support_info.description}",
                    style="white",
                )

        console.print()
        console.print("💡 Usage:", style="bold blue")
        console.print("   Use an alias with --model flag:", style="white")
        if official_models:
            example_model = official_models[0].friendly_name
        else:
            example_model = sorted_models[0].friendly_name
        console.print(f"   python -m prt_src.cli --model {example_model} chat", style="cyan")
        console.print(f"   python -m prt_src.tui --model {example_model}", style="cyan")
        console.print()
        console.print("📋 Legend:", style="bold blue")
        console.print("   ⭐ = Default model (used when --model not specified)", style="dim")
        console.print("   ✅ = Officially supported (all features work)", style="green")
        console.print("   🧪 = Experimental support (some features may not work)", style="yellow")
        console.print("   ❓ = Unsupported (use at your own risk)", style="dim")

    except Exception as e:
        console.print(f"✗ Failed to list models: {e}", style="red")
        console.print("\n💡 Troubleshooting:", style="bold blue")
        console.print("   • Ensure Ollama is installed: https://ollama.com/", style="dim")
        console.print("   • Start Ollama: brew services start ollama", style="dim")
        console.print("   • Check if models are installed: ollama list", style="dim")
        raise typer.Exit(1) from None


@app.command(name="prt-debug-info")
def prt_debug_info():
    """Display comprehensive system diagnostic information and exit."""
    from .debug_info import generate_debug_report

    try:
        report = generate_debug_report()
        console.print(report)
    except Exception as e:
        console.print(f"Error generating debug report: {e}", style="red")
        raise typer.Exit(1) from e
    # Exit successfully after displaying report
    raise typer.Exit(0)


# encrypt-db and decrypt-db commands removed as part of Issue #41


@app.command()
def db_status():
    """Check the database status."""
    status = check_setup_status()

    if status["needs_setup"]:
        console.print(f"PRT needs setup: {status['reason']}", style="yellow")
        raise typer.Exit(1) from None

    config = status["config"]
    db_path = Path(config.get("db_path", "prt_data/prt.db"))

    console.print(f"Database path: {db_path}", style="blue")
    # Encryption status removed as part of Issue #41

    if db_path.exists():
        try:
            db = create_database(db_path)

            if db.is_valid():
                console.print("Database status: [green]OK[/green]")
                console.print(f"Contacts: {db.count_contacts()}", style="green")
                console.print(f"Relationships: {db.count_relationships()}", style="green")
            else:
                console.print("Database status: [red]CORRUPT[/red]")
        except Exception as e:
            console.print(f"Database status: [red]ERROR[/red] - {e}")
    else:
        console.print("Database status: [yellow]NOT FOUND[/yellow]")


if __name__ == "__main__":
    app()
