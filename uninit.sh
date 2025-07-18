#!/bin/bash

# Check if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "Deactivating virtual environment..."
    deactivate
    echo "Virtual environment deactivated!"
else
    echo "No active virtual environment detected."
fi 