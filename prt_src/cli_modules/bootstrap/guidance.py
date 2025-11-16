"""
User guidance utilities for PRT CLI.

Functions for providing helpful guidance when database is empty or user needs direction.
These functions help orient users and provide clear next steps.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def show_empty_database_guidance():
    """Show helpful guidance when database is empty."""
    console = Console()

    guidance_text = Text()
    guidance_text.append("📭 No contacts found in your database.\n\n", style="yellow")
    guidance_text.append("🚀 To get started with PRT:\n", style="bold blue")
    guidance_text.append("   1. Import Google Takeout (option 3)\n", style="cyan")
    guidance_text.append("   2. This will populate your database with contacts\n", style="cyan")
    guidance_text.append(
        "   3. Then you can view, search, and manage relationships\n\n", style="cyan"
    )
    guidance_text.append(
        "💡 PRT works best when you have contacts to build relationships with!", style="green"
    )

    console.print(Panel(guidance_text, title="Getting Started", border_style="yellow"))
