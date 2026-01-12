#!/bin/bash

# setup_adws.sh - ADWS (AI Developer Workflow) Environment Setup
# This script sets up environment variables for the ADWS automation system

# Check if the script is being sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "This script must be sourced. Please run:"
    echo "    source ${0}"
    echo "or"
    echo "    . ${0}"
    exit 1
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}🤖 ADWS Environment Setup${NC}"
    echo "================================"
    echo ""
}

# Check command line arguments
COMMAND="$1"
case "$COMMAND" in
    --check)
        CHECK_ONLY=1
        ;;
    --reset)
        RESET_CONFIG=1
        ;;
    --help)
        echo "ADWS Environment Setup"
        echo ""
        echo "Usage:"
        echo "  source ./setup_adws.sh         # Interactive setup"
        echo "  source ./setup_adws.sh --check # Validate existing config"
        echo "  source ./setup_adws.sh --reset # Reconfigure everything"
        echo "  source ./setup_adws.sh --help  # Show this help"
        echo ""
        echo "Environment Variables:"
        echo "  GITHUB_REPO_URL    - GitHub repository URL (required)"
        echo "  ANTHROPIC_API_KEY  - Claude API key (required)"
        echo "  CLAUDE_CODE_PATH   - Path to Claude CLI (optional, defaults to 'claude')"
        echo "  GITHUB_PAT         - GitHub Personal Access Token (optional)"
        echo ""
        return 0
        ;;
esac

# Environment file path
ENV_FILE=".env"
ENV_EXAMPLE_FILE=".env.example"

# Load existing .env file if it exists
load_env_file() {
    if [[ -f "$ENV_FILE" ]]; then
        print_info "Loading existing environment from $ENV_FILE"
        set -a  # Mark variables for export
        source "$ENV_FILE"
        set +a  # Unmark variables for export
        return 0
    fi
    return 1
}

# Check if a command is available
check_command() {
    local cmd="$1"
    local name="$2"
    if command -v "$cmd" >/dev/null 2>&1; then
        print_success "$name is installed: $(which "$cmd")"
        return 0
    else
        print_error "$name is not installed"
        return 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    local all_good=1

    # Check GitHub CLI
    if ! check_command "gh" "GitHub CLI"; then
        print_error "GitHub CLI is required for ADWS"
        echo "Install with:"
        echo "  macOS: brew install gh"
        echo "  Ubuntu/Debian: sudo apt install gh"
        echo "  Windows: winget install --id GitHub.cli"
        all_good=0
    else
        # Check GitHub authentication
        if gh auth status >/dev/null 2>&1; then
            print_success "GitHub CLI is authenticated"
        else
            print_warning "GitHub CLI is not authenticated. Run: gh auth login"
        fi
    fi

    # Check Claude Code CLI
    local claude_path="${CLAUDE_CODE_PATH:-claude}"
    if ! check_command "$claude_path" "Claude Code CLI"; then
        print_error "Claude Code CLI is required for ADWS"
        echo "Install from: https://docs.anthropic.com/en/docs/claude-code"
        all_good=0
    fi

    # Check uv (Python package manager used by ADWS)
    if ! check_command "uv" "uv (Python package manager)"; then
        print_error "uv is required for ADWS"
        echo "Install with:"
        echo "  macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "  Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
        all_good=0
    fi

    if [[ $all_good -eq 0 ]]; then
        print_error "Please install missing prerequisites and run this script again"
        return 1
    fi

    print_success "All prerequisites are installed"
    return 0
}

# Validate API key format
validate_anthropic_key() {
    local key="$1"
    if [[ "$key" =~ ^sk-ant-[a-zA-Z0-9]{95,100}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Validate GitHub repository URL
validate_repo_url() {
    local url="$1"
    if [[ "$url" =~ ^https://github\.com/[^/]+/[^/]+/?$ ]]; then
        return 0
    else
        return 1
    fi
}

# Test API connectivity
test_anthropic_api() {
    local key="$1"
    print_info "Testing Anthropic API connectivity..."

    # Use Claude CLI to test the key
    local claude_path="${CLAUDE_CODE_PATH:-claude}"
    if ANTHROPIC_API_KEY="$key" "$claude_path" --help >/dev/null 2>&1; then
        print_success "Anthropic API key is valid"
        return 0
    else
        print_error "Failed to validate Anthropic API key"
        return 1
    fi
}

# Prompt for environment variable
# NOTE: All user-facing output goes to stderr (>&2) so that only the
# return value goes to stdout for command substitution capture.
prompt_for_var() {
    local var_name="$1"
    local description="$2"
    local current_value="$3"
    local is_secret="$4"
    local validator="$5"

    echo "" >&2
    echo "📝 $description" >&2

    if [[ -n "$current_value" ]]; then
        if [[ "$is_secret" == "true" ]]; then
            echo "Current value: $(echo "$current_value" | sed 's/./*/g')" >&2
        else
            echo "Current value: $current_value" >&2
        fi
        echo "Press Enter to keep current value, or enter new value:" >&2
    fi

    echo -n "$var_name: " >&2
    read -r user_input

    # Use current value if no input provided
    if [[ -z "$user_input" && -n "$current_value" ]]; then
        echo "$current_value"
        return 0
    fi

    # Validate input if validator provided
    if [[ -n "$validator" && -n "$user_input" ]]; then
        if ! "$validator" "$user_input"; then
            print_error "Invalid format for $var_name" >&2
            return 1
        fi
    fi

    echo "$user_input"
}

# Save environment variables to .env file
save_env_file() {
    print_info "Saving environment variables to $ENV_FILE"

    # Create backup if file exists
    if [[ -f "$ENV_FILE" ]]; then
        cp "$ENV_FILE" "${ENV_FILE}.backup"
        print_info "Created backup: ${ENV_FILE}.backup"
    fi

    # Set secure permissions
    touch "$ENV_FILE"
    chmod 600 "$ENV_FILE"

    # Write environment variables
    cat > "$ENV_FILE" << EOF
# ADWS Configuration - Auto-generated by setup_adws.sh
# Do not commit this file - it contains sensitive information

# Required Variables
GITHUB_REPO_URL=$GITHUB_REPO_URL
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

# Optional Variables
EOF

    # Add optional variables only if set
    if [[ -n "$CLAUDE_CODE_PATH" && "$CLAUDE_CODE_PATH" != "claude" ]]; then
        echo "CLAUDE_CODE_PATH=$CLAUDE_CODE_PATH" >> "$ENV_FILE"
    fi

    if [[ -n "$GITHUB_PAT" ]]; then
        echo "GITHUB_PAT=$GITHUB_PAT" >> "$ENV_FILE"
    fi

    print_success "Environment saved to $ENV_FILE"
}

# Check current configuration
check_config() {
    print_info "Checking current ADWS configuration..."

    local config_valid=1

    # Check required variables
    if [[ -z "$GITHUB_REPO_URL" ]]; then
        print_error "GITHUB_REPO_URL is not set"
        config_valid=0
    elif ! validate_repo_url "$GITHUB_REPO_URL"; then
        print_error "GITHUB_REPO_URL has invalid format: $GITHUB_REPO_URL"
        config_valid=0
    else
        print_success "GITHUB_REPO_URL: $GITHUB_REPO_URL"
    fi

    if [[ -z "$ANTHROPIC_API_KEY" ]]; then
        print_error "ANTHROPIC_API_KEY is not set"
        config_valid=0
    elif ! validate_anthropic_key "$ANTHROPIC_API_KEY"; then
        print_error "ANTHROPIC_API_KEY has invalid format"
        config_valid=0
    else
        print_success "ANTHROPIC_API_KEY: $(echo "$ANTHROPIC_API_KEY" | sed 's/./*/g')"
        # Test API connectivity
        if ! test_anthropic_api "$ANTHROPIC_API_KEY"; then
            config_valid=0
        fi
    fi

    # Check optional variables
    local claude_path="${CLAUDE_CODE_PATH:-claude}"
    print_success "CLAUDE_CODE_PATH: $claude_path"

    if [[ -n "$GITHUB_PAT" ]]; then
        print_success "GITHUB_PAT: $(echo "$GITHUB_PAT" | sed 's/./*/g')"
    else
        print_info "GITHUB_PAT: Using 'gh auth login' authentication"
    fi

    if [[ $config_valid -eq 1 ]]; then
        print_success "ADWS configuration is valid and ready to use!"
        echo ""
        echo "🚀 Quick Start:"
        echo "  cd adws"
        echo "  uv run adw_plan_build.py <issue-number>"
        echo ""
        return 0
    else
        print_error "ADWS configuration has issues"
        return 1
    fi
}

# Main setup function
setup_adws() {
    print_header

    # Check prerequisites first
    if ! check_prerequisites; then
        return 1
    fi

    # Load existing environment
    load_env_file

    # Handle different modes
    if [[ "$CHECK_ONLY" == "1" ]]; then
        check_config
        return $?
    fi

    if [[ "$RESET_CONFIG" == "1" ]]; then
        print_warning "Resetting ADWS configuration..."
        unset GITHUB_REPO_URL ANTHROPIC_API_KEY CLAUDE_CODE_PATH GITHUB_PAT
    fi

    # Interactive configuration
    print_info "Setting up ADWS environment variables..."
    echo "You'll be prompted for required and optional configuration."

    # Required variables
    local new_repo_url
    new_repo_url=$(prompt_for_var "GITHUB_REPO_URL" "GitHub repository URL (e.g., https://github.com/owner/repo)" "$GITHUB_REPO_URL" "false" "validate_repo_url")
    if [[ $? -ne 0 ]]; then
        print_error "Setup cancelled due to invalid repository URL"
        return 1
    fi
    export GITHUB_REPO_URL="$new_repo_url"

    local new_api_key
    new_api_key=$(prompt_for_var "ANTHROPIC_API_KEY" "Anthropic API key (starts with sk-ant-)" "$ANTHROPIC_API_KEY" "true" "validate_anthropic_key")
    if [[ $? -ne 0 ]]; then
        print_error "Setup cancelled due to invalid API key"
        return 1
    fi
    export ANTHROPIC_API_KEY="$new_api_key"

    # Test API before continuing
    if ! test_anthropic_api "$ANTHROPIC_API_KEY"; then
        print_error "Setup cancelled due to API connectivity issues"
        return 1
    fi

    # Optional variables
    echo ""
    print_info "Optional configuration (press Enter to skip):"

    local new_claude_path
    new_claude_path=$(prompt_for_var "CLAUDE_CODE_PATH" "Path to Claude CLI (optional, defaults to 'claude')" "$CLAUDE_CODE_PATH" "false" "")
    if [[ -n "$new_claude_path" ]]; then
        export CLAUDE_CODE_PATH="$new_claude_path"
    fi

    local new_github_pat
    new_github_pat=$(prompt_for_var "GITHUB_PAT" "GitHub Personal Access Token (optional, only if using different account than 'gh auth login')" "$GITHUB_PAT" "true" "")
    if [[ -n "$new_github_pat" ]]; then
        export GITHUB_PAT="$new_github_pat"
    fi

    # Save configuration
    save_env_file

    # Final validation
    echo ""
    check_config
}

# Run the setup
setup_adws