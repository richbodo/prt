#!/bin/bash
# Lint Helper Script for PRT
# Usage: ./scripts/lint.sh [--fix] [path]
#
# Runs linters (ruff + black) with clear output and next-step guidance.
# Automatically uses the virtual environment's tools.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Find the project root (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Determine which Python/tools to use
if [ -d "$PROJECT_ROOT/prt_env" ]; then
    PYTHON="$PROJECT_ROOT/prt_env/bin/python"
    RUFF="$PROJECT_ROOT/prt_env/bin/ruff"
    BLACK="$PROJECT_ROOT/prt_env/bin/black"
elif [ -n "$VIRTUAL_ENV" ]; then
    PYTHON="$VIRTUAL_ENV/bin/python"
    RUFF="$VIRTUAL_ENV/bin/ruff"
    BLACK="$VIRTUAL_ENV/bin/black"
else
    echo -e "${RED}Error: No virtual environment found.${NC}"
    echo "Please run: source ./init.sh"
    exit 1
fi

# Check if tools exist
if [ ! -f "$RUFF" ]; then
    echo -e "${RED}Error: ruff not found at $RUFF${NC}"
    echo "Please run: pip install ruff"
    exit 1
fi

if [ ! -f "$BLACK" ]; then
    echo -e "${RED}Error: black not found at $BLACK${NC}"
    echo "Please run: pip install black"
    exit 1
fi

# Parse arguments
FIX_MODE=0
TARGET_PATH="."

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix|-f)
            FIX_MODE=1
            shift
            ;;
        --help|-h)
            echo "Usage: ./scripts/lint.sh [--fix] [path]"
            echo ""
            echo "Options:"
            echo "  --fix, -f    Auto-fix issues where possible"
            echo "  --help, -h   Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./scripts/lint.sh                 # Check all files"
            echo "  ./scripts/lint.sh --fix           # Fix all files"
            echo "  ./scripts/lint.sh prt_src/        # Check specific directory"
            echo "  ./scripts/lint.sh --fix myfile.py # Fix specific file"
            exit 0
            ;;
        *)
            TARGET_PATH="$1"
            shift
            ;;
    esac
done

cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  PRT Lint Helper${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ERRORS_FOUND=0
FILES_MODIFIED=0

# Run ruff
echo -e "${YELLOW}Running ruff...${NC}"
if [ "$FIX_MODE" -eq 1 ]; then
    if $RUFF check --fix --show-fixes "$TARGET_PATH" 2>&1; then
        echo -e "${GREEN}✓ ruff: No issues${NC}"
    else
        RUFF_EXIT=$?
        if [ $RUFF_EXIT -eq 1 ]; then
            ERRORS_FOUND=1
            echo -e "${RED}✗ ruff: Issues found (some may have been fixed)${NC}"
            FILES_MODIFIED=1
        fi
    fi
else
    if $RUFF check "$TARGET_PATH" 2>&1; then
        echo -e "${GREEN}✓ ruff: No issues${NC}"
    else
        ERRORS_FOUND=1
        echo -e "${RED}✗ ruff: Issues found${NC}"
    fi
fi

echo ""

# Run black
echo -e "${YELLOW}Running black...${NC}"
if [ "$FIX_MODE" -eq 1 ]; then
    if $BLACK "$TARGET_PATH" 2>&1; then
        echo -e "${GREEN}✓ black: Formatted${NC}"
        FILES_MODIFIED=1
    fi
else
    if $BLACK --check "$TARGET_PATH" 2>&1; then
        echo -e "${GREEN}✓ black: No formatting needed${NC}"
    else
        ERRORS_FOUND=1
        echo -e "${RED}✗ black: Formatting needed${NC}"
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"

# Provide guidance based on results
if [ "$ERRORS_FOUND" -eq 1 ]; then
    echo -e "${RED}Issues found!${NC}"
    echo ""
    if [ "$FIX_MODE" -eq 0 ]; then
        echo -e "${YELLOW}Next steps:${NC}"
        echo "  1. Run with --fix to auto-fix what's possible:"
        echo "     ./scripts/lint.sh --fix"
        echo ""
        echo "  2. For remaining errors, fix manually and re-run"
        echo ""
        echo "  3. Some errors require --unsafe-fixes (use with caution):"
        echo "     $RUFF check --fix --unsafe-fixes $TARGET_PATH"
    else
        echo -e "${YELLOW}Next steps:${NC}"
        echo "  Some errors couldn't be auto-fixed. Fix them manually, then:"
        echo ""
        echo "  1. Stage your changes:  git add -u"
        echo "  2. Commit again:        git commit"
        echo ""
        echo "  For unsafe fixes (use with caution):"
        echo "     $RUFF check --fix --unsafe-fixes $TARGET_PATH"
    fi
    exit 1
elif [ "$FILES_MODIFIED" -eq 1 ]; then
    echo -e "${GREEN}All issues fixed!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Stage your changes:  git add -u"
    echo "  2. Commit again:        git commit"
    exit 0
else
    echo -e "${GREEN}All checks passed!${NC}"
    exit 0
fi
