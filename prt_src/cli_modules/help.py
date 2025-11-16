"""
Help system for PRT CLI.

This module provides centralized help text and option definitions
to ensure consistency across all CLI commands and help displays.
"""

from pathlib import Path
from typing import Any
from typing import Dict

# CLI option definitions - single source of truth
CLI_OPTIONS: Dict[str, Dict[str, Any]] = {
    "debug": {
        "help": "Run with sample data (safe, isolated database)",
        "flag": "--debug",
        "short_flag": "-d",
    },
    "regenerate_fixtures": {
        "help": "Reset sample data (use with --debug)",
        "flag": "--regenerate-fixtures",
    },
    "setup": {
        "help": "First-time setup: import contacts or try demo data",
        "flag": "--setup",
    },
    "cli": {
        "help": "Use command-line interface instead of TUI",
        "flag": "--cli",
    },
    "tui": {
        "help": "Use TUI interface (default)",
        "flag": "--tui",
    },
    "model": {
        "help": "Choose AI model (e.g. 'gpt-oss-20b', 'mistral-7b-instruct')",
        "flag": "--model",
        "short_flag": "-m",
        "metavar": "MODEL",
    },
    "chat": {
        "help": "Start AI chat mode. Provide query text or use --chat='' for interactive mode",
        "flag": "--chat",
        "metavar": "[TEXT]",
    },
}


def load_help_text() -> str:
    """Load the main help text from the markdown file."""
    help_file = Path(__file__).parent / "help_text.md"
    try:
        return help_file.read_text()
    except FileNotFoundError:
        return "Help text not found. Please check CLI installation."


def print_custom_help():
    """Print clean, accessible help text without Rich formatting."""
    help_content = load_help_text()

    # Convert markdown to plain text for terminal display
    lines = help_content.split("\n")
    output_lines = []

    for line in lines:
        # Convert markdown headers to plain text
        if line.startswith("# "):
            output_lines.append(line[2:].upper())
            output_lines.append("=" * len(line[2:]))
        elif line.startswith("## "):
            output_lines.append("")
            output_lines.append(line[3:].upper())
            output_lines.append("-" * len(line[3:]))
        elif line.startswith("**") and line.endswith("**"):
            # Convert **bold** to plain text
            output_lines.append(line.replace("**", ""))
        elif line.startswith("- `") and line.endswith("`"):
            # Convert list items with code
            cleaned = line.replace("`", "").replace("- ", "  ")
            output_lines.append(cleaned)
        elif line.startswith("```"):
            # Skip code block markers
            continue
        else:
            output_lines.append(line)

    # Add usage line at the top
    final_output = ["Usage: python -m prt_src [OPTIONS] [COMMAND]", ""]
    final_output.extend(output_lines)

    print("\n".join(final_output))


def get_option_help(option_name: str) -> str:
    """Get help text for a specific option."""
    option = CLI_OPTIONS.get(option_name)
    if not option:
        return f"Unknown option: {option_name}"
    return option["help"]


def get_option_flags(option_name: str) -> tuple[str, str]:
    """Get the flag and short flag for an option."""
    option = CLI_OPTIONS.get(option_name)
    if not option:
        return ("", "")

    flag = option["flag"]
    short_flag = option.get("short_flag", "")
    return (flag, short_flag)
