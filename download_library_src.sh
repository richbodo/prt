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
#
# OPTIONS:
#   --list, -l    Display inventory of defined vs. downloaded libraries
#   --help, -h    Display this help message
#
# USAGE:
#   ./download_library_src.sh           # Clone all libraries
#   ./download_library_src.sh --list    # Show library inventory
#   ./download_library_src.sh --help    # Show help
# ==============================================================================

# Define the target directory for all repositories
TARGET_DIR="EXTERNAL_DOCS"

# =============================================================================
# HELPER FUNCTIONS FOR --list OPTION
# =============================================================================

# Display help message
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Download external library repositories to $TARGET_DIR/"
    echo ""
    echo "OPTIONS:"
    echo "  --list, -l    Display inventory of defined vs. downloaded libraries"
    echo "  --help, -h    Display this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0              Clone all defined libraries"
    echo "  $0 --list       Show which libraries are available/missing"
    echo ""
}

# Get list of libraries defined in this script (from clone_repo calls)
get_defined_libraries() {
    # Extract repository paths from clone_repo calls and get the last component (library name)
    # Only match lines that start with optional whitespace followed by clone_repo
    grep '^[[:space:]]*clone_repo "' "$0" | \
        awk -F'"' '{print $2}' | \
        awk -F'/' '{print $NF}' | \
        grep -v '^$' | \
        sort | \
        uniq
}

# Get list of libraries currently downloaded in EXTERNAL_DOCS
get_downloaded_libraries() {
    if [ ! -d "$TARGET_DIR" ]; then
        return
    fi

    # List directories in EXTERNAL_DOCS, excluding hidden files/directories
    find "$TARGET_DIR" -maxdepth 1 -type d -not -name ".*" -not -name "$TARGET_DIR" -exec basename {} \; | \
        sort
}

# Display library inventory with status indicators
display_library_status() {
    local -a defined_libs
    local -a downloaded_libs
    local -a available_libs
    local -a missing_libs
    local -a unlisted_libs

    # Read libraries into arrays (using portable method)
    while IFS= read -r lib; do
        defined_libs+=("$lib")
    done < <(get_defined_libraries)

    while IFS= read -r lib; do
        downloaded_libs+=("$lib")
    done < <(get_downloaded_libraries)

    # Categorize libraries
    for lib in "${defined_libs[@]}"; do
        if printf '%s\n' "${downloaded_libs[@]}" | grep -q "^${lib}$"; then
            available_libs+=("$lib")
        else
            missing_libs+=("$lib")
        fi
    done

    for lib in "${downloaded_libs[@]}"; do
        if ! printf '%s\n' "${defined_libs[@]}" | grep -q "^${lib}$"; then
            unlisted_libs+=("$lib")
        fi
    done

    # Display header
    echo ""
    echo "=========================================="
    echo "EXTERNAL LIBRARY INVENTORY"
    echo "=========================================="
    echo ""
    echo "Summary:"
    echo "  Total Defined:    ${#defined_libs[@]}"
    echo "  Available:        ${#available_libs[@]}"
    echo "  Missing:          ${#missing_libs[@]}"
    echo "  Unlisted:         ${#unlisted_libs[@]}"
    echo ""

    # Display available libraries
    if [ ${#available_libs[@]} -gt 0 ]; then
        echo "✅ Available Libraries (${#available_libs[@]}):"
        for lib in "${available_libs[@]}"; do
            echo "   ✅ $lib"
        done
        echo ""
    fi

    # Display missing libraries
    if [ ${#missing_libs[@]} -gt 0 ]; then
        echo "❌ Missing Libraries (${#missing_libs[@]}):"
        for lib in "${missing_libs[@]}"; do
            echo "   ❌ $lib"
        done
        echo ""
    fi

    # Display unlisted libraries
    if [ ${#unlisted_libs[@]} -gt 0 ]; then
        echo "⚠️  Unlisted Libraries (${#unlisted_libs[@]}):"
        echo "   (Present in $TARGET_DIR/ but not defined in this script)"
        for lib in "${unlisted_libs[@]}"; do
            echo "   ⚠️  $lib"
        done
        echo ""
    fi

    echo "=========================================="
    echo ""
}

# =============================================================================
# MAIN CLONE FUNCTION
# =============================================================================

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

# =============================================================================
# ARGUMENT PARSING
# =============================================================================

# Check for command-line arguments
if [ $# -gt 0 ]; then
    case "$1" in
        --list|-l)
            display_library_status
            exit 0
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option '$1'"
            echo ""
            show_help
            exit 1
            ;;
    esac
fi

# =============================================================================
# MAIN CLONE OPERATION
# =============================================================================

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
