"""
TUI __main__ module for running PRT TUI with command-line arguments.

This module allows running the TUI directly with:
    python -m prt_src.tui [options]

Example usage:
    python -m prt_src.tui
    python -m prt_src.tui --debug
    python -m prt_src.tui --model llama8
    python -m prt_src.tui --model gpt-oss-20b
"""

import argparse
import sys

from prt_src.tui.app import PRTApp


def main():
    """Main entry point for TUI with command-line argument support."""
    parser = argparse.ArgumentParser(
        description="Personal Relationship Toolkit (PRT) - Text User Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings (from config)
  python -m prt_src.tui

  # Run in debug mode with fixture data
  python -m prt_src.tui --debug

  # Use friendly model alias (auto-detects provider)
  python -m prt_src.tui --model llama8
  python -m prt_src.tui --model gpt-oss-20b

  # Force setup screen
  python -m prt_src.tui --setup
""",
    )

    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Run in debug mode with fixture data",
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Force setup screen even if database has data",
    )

    parser.add_argument(
        "--model",
        "-m",
        type=str,
        help="Model alias to use (e.g., 'gpt-oss-20b', 'mistral-7b-instruct'). Use CLI 'list-models' command to see available options.",
    )

    args = parser.parse_args()

    # Create and run TUI application
    try:
        app = PRTApp(
            debug=args.debug,
            force_setup=args.setup,
            model=args.model,
        )
        app.run()
    except KeyboardInterrupt:
        print("\nExiting...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
