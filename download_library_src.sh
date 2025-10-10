#!/bin/bash

# ==============================================================================
# Script to download project library repositories from GitHub into a dedicated
# subdirectory.
#
# This script will:
# 1. Create a directory named 'EXTERNAL_DOCS/' if it doesn't exist.
# 2. Change into that directory.
# 3. Perform a shallow clone (`--depth 1`) for each repository.
# 4. Skip any repository that has already been cloned.
# ==============================================================================

# Define the target directory for all repositories
TARGET_DIR="EXTERNAL_DOCS"

# Function to clone a Git repository
clone_repo() {
    local repo_path=$1
    local target_dir=$(basename "$repo_path") # Extract repo name for the directory

    echo "--------------------------------------------------"

    if [ -d "$target_dir" ]; then
        echo "✅ Directory '$target_dir' already exists. Skipping."
    else
        echo "Cloning $repo_path..."
        git clone --depth 1 "https://github.com/$repo_path.git"
        if [ $? -eq 0 ]; then
            echo "👍 Successfully cloned into './$target_dir/'."
        else
            echo "❌ Failed to clone $repo_path."
        fi
    fi
}

echo "🚀 Starting download of project library repositories..."
echo "All repositories will be cloned into the '$TARGET_DIR/' directory."

# Create the target directory if it doesn't exist
mkdir -p "$TARGET_DIR"

# Change into the target directory. Exit script if cd fails.
cd "$TARGET_DIR" || exit

# --- Core TUI & CLI Libraries ---
clone_repo "tiangolo/typer"
clone_repo "Textualize/textual"
clone_repo "Textualize/rich"

# --- Data & Web Libraries ---
clone_repo "sqlalchemy/sqlalchemy"
clone_repo "sqlalchemy/sqlalchemy-docs" # SQLAlchemy's separate docs repo
clone_repo "psf/requests"
clone_repo "ollama/ollama"

# --- Google API Stack ---
clone_repo "googleapis/google-auth-library-python"
clone_repo "googleapis/google-auth-library-python-oauthlib"
clone_repo "googleapis/google-api-python-client"

# --- Search, Caching & Data Parsing ---
clone_repo "google/pygtrie"
clone_repo "amitdev/lru-dict"
clone_repo "eventable/vobject"

# --- ML & Image Processing ---
clone_repo "huggingface/transformers"
clone_repo "pytorch/pytorch"
clone_repo "python-pillow/Pillow"

# --- Testing & Tooling ---
clone_repo "pytest-dev/pytest"
clone_repo "pytest-dev/pytest-asyncio"
clone_repo "promptfoo/promptfoo"

echo "--------------------------------------------------"
echo ""
echo "✨ All cloning tasks complete."
echo "All files are located in the '$TARGET_DIR/' directory."
