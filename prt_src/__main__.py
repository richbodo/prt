"""Entry point for python -m prt_src execution.

This module allows running PRT as a module with:
python -m prt_src

Also serves as the console script entry point when installed via pip.
"""

from prt_src.cli import app


def main():
    """Main entry point for console script and module execution."""
    app()


if __name__ == "__main__":
    main()
