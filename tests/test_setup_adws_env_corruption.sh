#!/bin/bash

# test_setup_adws_env_corruption.sh - Regression test to prevent .env file corruption
# This script validates that the setup_adws.sh script creates properly formatted .env files

# Color codes for test output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Test output functions
test_info() {
    echo -e "${BLUE}ℹ️  TEST: $1${NC}"
}

test_pass() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
}

test_fail() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
}

test_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

# Helper function to validate .env file format
validate_env_file_format() {
    local env_file="$1"

    if [[ ! -f "$env_file" ]]; then
        echo "File does not exist"
        return 1
    fi

    # Check that file has valid shell syntax
    if ! bash -n "$env_file" 2>/dev/null; then
        echo "Invalid shell syntax"
        return 1
    fi

    # Check for corruption indicators (prompts, ANSI codes, interactive text)
    if grep -q "📝\|Current value:\|Press Enter\|Auto-detected" "$env_file"; then
        echo "Contains interactive prompts"
        return 1
    fi

    # Check for ANSI color codes
    if grep -q $'\033\[' "$env_file"; then
        echo "Contains ANSI color codes"
        return 1
    fi

    # Check that all non-comment, non-empty lines are valid variable assignments
    while IFS= read -r line; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

        # Check if line is a valid variable assignment
        if [[ ! "$line" =~ ^[A-Z_][A-Z0-9_]*= ]]; then
            echo "Invalid variable assignment: $line"
            return 1
        fi
    done < "$env_file"

    return 0
}

# Test that current .env file is properly formatted
test_current_env_file_format() {
    test_info "Validating current .env file format"

    local validation_result
    validation_result=$(validate_env_file_format ".env")
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        test_pass "Current .env file has proper format"
    else
        test_fail "Current .env file has invalid format: $validation_result"
    fi
}

# Test that .env file can be sourced without errors
test_env_file_sourcing() {
    test_info "Testing .env file can be sourced without errors"

    if source .env 2>/dev/null; then
        test_pass ".env file sources successfully"
    else
        test_fail ".env file cannot be sourced"
    fi
}

# Test that required variables are loaded from .env
test_env_variables_loading() {
    test_info "Testing environment variables load correctly"

    # Source the .env file in a subshell to avoid affecting current environment
    local github_url anthropic_key
    eval "$(source .env 2>/dev/null && echo "github_url=\$GITHUB_REPO_URL"; echo "anthropic_key=\$ANTHROPIC_API_KEY")"

    if [[ -n "$github_url" ]]; then
        test_pass "GITHUB_REPO_URL loads correctly: $github_url"
    else
        test_fail "GITHUB_REPO_URL not loaded from .env file"
    fi

    if [[ -n "$anthropic_key" ]]; then
        test_pass "ANTHROPIC_API_KEY loads correctly (length: ${#anthropic_key})"
    else
        test_fail "ANTHROPIC_API_KEY not loaded from .env file"
    fi
}

# Test the prompt_for_var function output isolation
test_prompt_function_isolation() {
    test_info "Testing prompt_for_var function output isolation"

    # Create a temporary script to test the function
    local temp_script="/tmp/test_prompt_isolation_$$.sh"
    cat > "$temp_script" << 'EOF'
#!/bin/bash
cd /Users/richardbodo/src/prt
cp setup_adws.sh /tmp/setup_func_test.sh
sed -i.bak '/^# Run the setup$/d; /^setup_adws$/d' /tmp/setup_func_test.sh
source /tmp/setup_func_test.sh

# Test the function with a known value
result=$(echo "" | prompt_for_var "TEST_VAR" "Test variable" "expected-value" "false" "" "" 2>/dev/null)
echo "$result"
rm -f /tmp/setup_func_test.sh /tmp/setup_func_test.sh.bak
EOF

    chmod +x "$temp_script"
    local result
    result=$("$temp_script" 2>/dev/null)

    if [[ "$result" == "expected-value" ]]; then
        test_pass "prompt_for_var outputs only the intended value"
    else
        test_fail "prompt_for_var outputs unexpected content: '$result'"
    fi

    rm -f "$temp_script"
}

# Test that setup script help still works
test_setup_help_functionality() {
    test_info "Testing setup script help functionality"

    if source ./setup_adws.sh --help >/dev/null 2>&1; then
        test_pass "Setup script help command works"
    else
        test_fail "Setup script help command fails"
    fi
}

# Test setup script check functionality
test_setup_check_functionality() {
    test_info "Testing setup script check functionality"

    # The check may fail due to invalid API key, but it should not produce shell errors
    local output
    output=$(source ./setup_adws.sh --check 2>&1)
    local exit_code=$?

    # Check for shell syntax errors that indicate .env corruption
    if echo "$output" | grep -q "command not found\|unknown file attribute\|bad pattern"; then
        test_fail "Setup check produces shell syntax errors indicating .env corruption"
    else
        test_pass "Setup check runs without shell syntax errors"
    fi

    # Check that environment variables are recognized
    if echo "$output" | grep -q "GITHUB_REPO_URL.*https://github.com/richbodo/prt"; then
        test_pass "Setup check recognizes GITHUB_REPO_URL correctly"
    else
        test_fail "Setup check does not recognize GITHUB_REPO_URL"
    fi
}

# Main test execution
main() {
    echo ""
    echo -e "${BLUE}🧪 ADWS Setup Environment Corruption Regression Test${NC}"
    echo "======================================================="
    echo ""

    # Ensure we're in the right directory
    if [[ ! -f "setup_adws.sh" ]]; then
        echo -e "${RED}Error: setup_adws.sh not found. Please run this test from the project root.${NC}"
        exit 1
    fi

    # Ensure .env file exists
    if [[ ! -f ".env" ]]; then
        echo -e "${RED}Error: .env file not found. Please ensure a valid .env file exists.${NC}"
        exit 1
    fi

    # Run all tests
    test_current_env_file_format
    echo ""

    test_env_file_sourcing
    echo ""

    test_env_variables_loading
    echo ""

    test_prompt_function_isolation
    echo ""

    test_setup_help_functionality
    echo ""

    test_setup_check_functionality
    echo ""

    # Show test summary
    echo "======================================================="
    echo -e "${BLUE}📊 Test Summary${NC}"
    echo "======================================================="
    echo "Total tests: $TESTS_TOTAL"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    echo ""

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}🎉 All tests passed! No .env corruption detected.${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed. .env file corruption may be present.${NC}"
        exit 1
    fi
}

# Check if script is being executed (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi