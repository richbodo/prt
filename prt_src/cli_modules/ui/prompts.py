"""
Prompt utilities for PRT CLI.

Functions for handling user input prompts with validation and smart continuation.
These utilities provide consistent prompt behavior across the CLI.
"""

from datetime import date
from datetime import datetime

from rich.console import Console
from rich.prompt import Confirm
from rich.prompt import Prompt


def smart_continue_prompt(operation_type: str):
    """Smart continuation prompt - only when data would scroll off screen."""
    # Only prompt for operations that display lots of data that user needs time to review
    prompt_when_data_heavy = [
        "v",  # View contacts - displays table that might be long
        "i",  # Import - shows import results that user should review
    ]

    # Everything else: menus, quick operations, errors - no prompting needed
    # User can navigate at their own pace
    if operation_type in prompt_when_data_heavy:
        Prompt.ask("\nPress Enter to continue", default="")
    # Default: no prompt - let user flow naturally through menus


def _get_valid_date(prompt_text: str) -> date | None:
    """Get a valid date from user input with retry logic."""
    console = Console()

    while True:
        date_str = Prompt.ask(prompt_text)
        if not date_str:  # Empty input means skip
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            console.print("Invalid date format. Please use YYYY-MM-DD format.", style="red")
            if not Confirm.ask("Try again?", default=True):
                return None
