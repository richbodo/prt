"""
Debug command for PRT CLI.

This module contains the debug information command for system diagnostics.
"""

import typer
from rich.console import Console

console = Console()


def prt_debug_info_command():
    """Display comprehensive system diagnostic information and exit."""
    from ...debug_info import generate_debug_report

    try:
        report = generate_debug_report()
        console.print(report)
    except Exception as e:
        console.print(f"Error generating debug report: {e}", style="red")
        raise typer.Exit(1) from e
    # Exit successfully after displaying report
    raise typer.Exit(0)
