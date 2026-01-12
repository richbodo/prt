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

# Clean up ADWS environment variables
if [ -n "$GITHUB_REPO_URL" ] || [ -n "$ANTHROPIC_API_KEY" ] || [ -n "$GITHUB_PAT" ] || [ -n "$CLAUDE_CODE_PATH" ]; then
    echo "Cleaning up ADWS environment variables..."
    unset GITHUB_REPO_URL
    unset ANTHROPIC_API_KEY
    unset GITHUB_PAT
    unset CLAUDE_CODE_PATH
    echo "ADWS environment variables cleaned up!"
    echo "Note: .env file preserved for next session"
fi
