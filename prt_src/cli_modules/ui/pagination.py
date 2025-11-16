"""
Pagination utilities for PRT CLI.

Functions for handling paginated displays of search results and lists.
These utilities provide consistent navigation patterns across the CLI.
"""

from rich.console import Console
from rich.prompt import Prompt


def paginate_results(items: list, items_per_page: int = 24) -> None:
    """Paginate through a list of items with navigation."""
    console = Console()

    if not items:
        return

    total_pages = (len(items) + items_per_page - 1) // items_per_page
    current_page = 0

    while True:
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(items))
        page_items = items[start_idx:end_idx]

        # Display current page items
        for item in page_items:
            if callable(item):
                item()  # Execute function to display item
            else:
                console.print(item)

        # Show pagination info
        console.print(
            f"\nPage {current_page + 1} of {total_pages} | Showing {start_idx + 1}-{end_idx} of {len(items)} results",
            style="dim",
        )

        # Build navigation options dynamically
        nav_choices = []
        nav_descriptions = []

        if current_page > 0:
            nav_choices.append("p")
            nav_descriptions.append("(p)revious")

        if current_page < total_pages - 1:
            nav_choices.append("n")
            nav_descriptions.append("(n)ext")

        nav_choices.append("e")  # export
        nav_descriptions.append("(e)xport")

        nav_choices.append("q")  # quit
        nav_descriptions.append("(q)uit")

        # Create a compact, terminal-friendly prompt
        nav_text = " | ".join(nav_descriptions)
        prompt_text = f"Navigation: {nav_text}"

        # Use a shorter prompt if it's too long
        if len(prompt_text) > 60:
            nav_short = "/".join([f"{choice}" for choice in nav_choices])
            prompt_text = f"Options [{nav_short}]"

        choice = Prompt.ask(prompt_text, choices=nav_choices, default="q")

        if choice == "q":
            break
        elif choice == "n" and current_page < total_pages - 1:
            current_page += 1
        elif choice == "p" and current_page > 0:
            current_page -= 1
        elif choice == "e":
            return "export"  # Signal to calling function to handle export
