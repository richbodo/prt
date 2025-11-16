"""
Formatting utilities for PRT CLI.

Functions for displaying content with consistent formatting and styling.
These utilities provide reusable display patterns across the CLI.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text


def show_full_note(title: str, content: str) -> None:
    """Show full note content with scrolling capability."""
    console = Console()

    note_text = Text()
    note_text.append(f"Note: {title}\n", style="bold cyan")
    note_text.append("=" * 50 + "\n", style="blue")
    note_text.append(content, style="white")

    console.print(Panel(note_text, title=f"Full Note: {title}", border_style="cyan"))
    Prompt.ask("\nPress Enter to return to search results")
