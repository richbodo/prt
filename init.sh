#!/bin/bash

# Check if the script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script must be sourced. Please run:"
    echo "    source ${0}"
    echo "or"
    echo "    . ${0}"
    exit 1
fi

# Detect platform
UNAME_OUT="$(uname -s)"
echo "Os is: "
echo $UNAME_OUT

case "$UNAME_OUT" in
    Darwin*) OS="mac" ;;
    Linux*) OS="linux" ;;
    *) echo "Unsupported operating system: $UNAME_OUT"; return 1 ;;
esac

if [ "$OS" = "mac" ]; then
    echo "Os is: "
    echo $OS	
    echo "Checking for Homebrew..."
    # macOS uses Homebrew for dependencies
    if ! command -v brew >/dev/null; then
        echo "Error: Homebrew is required but not installed. Please install Homebrew first."
        echo "Visit https://brew.sh for installation instructions."
        return 1
    fi
    echo "Homebrew found at: $(which brew)"

    # SQLCipher installation removed as part of Issue #41
    echo "SQLCipher dependencies removed - using regular SQLite now"
elif [ "$OS" = "linux" ]; then
    # Linux installation using apt for Debian-based systems
    if command -v apt-get >/dev/null; then
        echo "Installing system dependencies via apt..."
        if [ "$EUID" -ne 0 ] && command -v sudo >/dev/null; then
            sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-dev build-essential pkg-config || { echo "Failed to install system packages"; return 1; }
        else
            apt-get update && apt-get install -y python3 python3-venv python3-dev build-essential pkg-config || { echo "Failed to install system packages"; return 1; }
        fi
    else
        echo "Error: apt-get not found. Please install required dependencies manually."
        return 1
    fi

    # SQLCipher flags removed as part of Issue #41
fi

# Check if virtual environment exists, if not create it
if [ ! -d "prt_env" ]; then
    echo "Creating new virtual environment: prt_env"
    python3 -m venv prt_env || { echo "Failed to create virtual environment"; exit 1; }
    
    # Activate and install requirements
    source prt_env/bin/activate || { echo "Failed to activate virtual environment"; return 1; }
    # Verify we're in the virtual environment before installing
    if [ "$VIRTUAL_ENV" != "$(pwd)/prt_env" ]; then
        echo "Error: Virtual environment not properly activated"
        return 1
    fi
    # Install requirements with verbose output
    pip install -v -r requirements.txt || { echo "Failed to install requirements"; return 1; }
    echo "Installed required packages"
else
    # Just activate if it already exists
    source prt_env/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }
fi

# Verify we're in the virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Virtual environment activated! You should see (prt_env) in your prompt."
    echo "If you don't see (prt_env), try running: source prt_env/bin/activate"

    # Install development requirements (including pre-commit)
    if [ -f "requirements-dev.txt" ]; then
        pip install -v -r requirements-dev.txt || { echo "Failed to install development requirements"; return 1; }
        pre-commit install || { echo "Failed to install pre-commit hooks"; return 1; }

        # Optionally run pre-commit across the codebase to establish a baseline
        if [ "${RUN_PRE_COMMIT:-0}" = "1" ]; then
            pre-commit run --all-files || { echo "pre-commit run failed"; return 1; }
        fi
    fi
else
    echo "Warning: Virtual environment not properly activated"
fi
