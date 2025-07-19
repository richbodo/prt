#!/bin/bash

# Check if the script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script must be sourced. Please run:"
    echo "    source ${0}"
    echo "or"
    echo "    . ${0}"
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d "prt_env" ]; then
    echo "Creating new virtual environment: prt_env"
    python3 -m venv prt_env || { echo "Failed to create virtual environment"; exit 1; }
    
    # Activate and install requirements
    source prt_env/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }
    pip install -r requirements.txt || { echo "Failed to install requirements"; exit 1; }
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