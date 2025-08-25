#!/bin/bash

# Check if the script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script must be sourced. Please run:"
    echo "    source ${0}"
    echo "or"
    echo "    . ${0}"
    exit 1
fi

# Check if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Deactivating virtual environment..."
    deactivate
    echo "Virtual environment deactivated!"
else
    echo "No active virtual environment detected."
fi

# Clean up SQLCipher environment variables
if [ -n "$SQLCIPHER_PATH" ]; then
    echo "Cleaning up SQLCipher environment variables..."
    unset SQLCIPHER_PATH
    unset LDFLAGS
    unset CPPFLAGS
    echo "SQLCipher environment variables cleaned up!"
fi
