#!/bin/bash

# Check if the script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script must be sourced. Please run:"
    echo "    source ${0}"
    echo "or"
    echo "    . ${0}"
    exit 1
fi

# Check if brew is installed
if ! command -v brew &> /dev/null; then
    echo "Error: Homebrew is required but not installed. Please install Homebrew first."
    echo "Visit https://brew.sh for installation instructions."
    return 1
fi

# Check if sqlcipher is installed via brew
if ! brew list sqlcipher &> /dev/null; then
    echo "Installing sqlcipher via Homebrew..."
    brew install sqlcipher || { echo "Failed to install sqlcipher"; return 1; }
fi

# Set SQLCipher environment variables
export SQLCIPHER_PATH=$(brew --prefix sqlcipher)
export LDFLAGS="-L$SQLCIPHER_PATH/lib"
export CPPFLAGS="-I$SQLCIPHER_PATH/include"

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
else
    echo "Warning: Virtual environment not properly activated"
fi 