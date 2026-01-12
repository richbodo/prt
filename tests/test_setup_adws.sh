#!/bin/bash

# test_setup_adws.sh - Test suite for ADWS setup auto-detection functionality
# This script validates the auto-detection features and error handling

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

# Source the setup script to access its functions
source_setup_script() {
    # Create a temporary copy to avoid executing the main script
    local temp_script="/tmp/setup_adws_test.sh"
    cp setup_adws.sh "$temp_script"

    # Remove the execution line at the end
    sed -i.bak '/^# Run the setup$/d; /^setup_adws$/d' "$temp_script"

    source "$temp_script"
    rm -f "$temp_script" "${temp_script}.bak"
}

# Test the convert_ssh_to_https function
test_ssh_url_conversion() {
    test_info "Testing SSH to HTTPS URL conversion"

    # Test SSH format: git@github.com:user/repo.git
    local result=$(convert_ssh_to_https "git@github.com:user/repo.git")
    if [[ "$result" == "https://github.com/user/repo" ]]; then
        test_pass "SSH URL with .git suffix converted correctly"
    else
        test_fail "SSH URL conversion failed. Expected: https://github.com/user/repo, Got: $result"
    fi

    # Test SSH format without .git suffix
    result=$(convert_ssh_to_https "git@github.com:user/repo")
    if [[ "$result" == "https://github.com/user/repo" ]]; then
        test_pass "SSH URL without .git suffix converted correctly"
    else
        test_fail "SSH URL conversion failed. Expected: https://github.com/user/repo, Got: $result"
    fi

    # Test SSH format with ssh:// prefix
    result=$(convert_ssh_to_https "ssh://git@github.com/user/repo.git")
    if [[ "$result" == "https://github.com/user/repo" ]]; then
        test_pass "SSH URL with ssh:// prefix converted correctly"
    else
        test_fail "SSH URL conversion failed. Expected: https://github.com/user/repo, Got: $result"
    fi

    # Test HTTPS URL (should remain unchanged)
    result=$(convert_ssh_to_https "https://github.com/user/repo")
    if [[ "$result" == "https://github.com/user/repo" ]]; then
        test_pass "HTTPS URL remained unchanged"
    else
        test_fail "HTTPS URL modification failed. Expected: https://github.com/user/repo, Got: $result"
    fi
}

# Test the extract_repo_info function
test_repo_info_extraction() {
    test_info "Testing repository information extraction"

    # Test in current git repository (if available)
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        local result=$(extract_repo_info "origin")
        if [[ $? -eq 0 && -n "$result" ]]; then
            test_pass "Successfully extracted repository info from current git repo"
            test_info "Extracted URL: $result"
        else
            test_warning "Could not extract repository info from current repo (this may be expected)"
        fi
    else
        test_warning "Not in a git repository - skipping extraction test"
    fi

    # Test with non-existent remote
    local result
    result=$(extract_repo_info "nonexistent-remote" 2>/dev/null)
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        test_pass "Correctly failed for non-existent remote"
    else
        test_fail "Should have failed for non-existent remote (exit code: $exit_code, result: '$result')"
    fi
}

# Test the GitHub URL validation function
test_github_url_validation() {
    test_info "Testing GitHub URL validation"

    # Valid URLs
    if validate_repo_url "https://github.com/user/repo"; then
        test_pass "Valid GitHub URL accepted"
    else
        test_fail "Valid GitHub URL rejected"
    fi

    if validate_repo_url "https://github.com/user/repo/"; then
        test_pass "Valid GitHub URL with trailing slash accepted"
    else
        test_fail "Valid GitHub URL with trailing slash rejected"
    fi

    # Invalid URLs
    if ! validate_repo_url "https://gitlab.com/user/repo"; then
        test_pass "GitLab URL correctly rejected"
    else
        test_fail "GitLab URL incorrectly accepted"
    fi

    if ! validate_repo_url "git@github.com:user/repo.git"; then
        test_pass "SSH URL correctly rejected (needs conversion first)"
    else
        test_fail "SSH URL incorrectly accepted"
    fi

    if ! validate_repo_url "https://github.com/user"; then
        test_pass "Incomplete GitHub URL correctly rejected"
    else
        test_fail "Incomplete GitHub URL incorrectly accepted"
    fi
}

# Test the detect_github_repo_url function
test_github_repo_detection() {
    test_info "Testing GitHub repository URL auto-detection"

    # This test depends on being in a git repository with GitHub remote
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        local result=$(detect_github_repo_url "false" 2>/dev/null)
        local exit_code=$?

        if [[ $exit_code -eq 0 && -n "$result" ]]; then
            # Validate that the detected URL is a valid GitHub URL
            if validate_repo_url "$result"; then
                test_pass "Auto-detected valid GitHub repository URL: $result"
            else
                test_fail "Auto-detected URL is not a valid GitHub URL: $result"
            fi
        else
            test_warning "Auto-detection failed (this may be expected if no GitHub remote exists)"
        fi
    else
        test_warning "Not in a git repository - skipping auto-detection test"
    fi
}

# Test that the .env.example file exists
test_env_example_exists() {
    test_info "Testing .env.example file existence"

    if [[ -f ".env.example" ]]; then
        test_pass ".env.example file exists"

        # Check if it contains expected variables
        if grep -q "GITHUB_REPO_URL" ".env.example"; then
            test_pass ".env.example contains GITHUB_REPO_URL"
        else
            test_fail ".env.example does not contain GITHUB_REPO_URL"
        fi

        if grep -q "ANTHROPIC_API_KEY" ".env.example"; then
            test_pass ".env.example contains ANTHROPIC_API_KEY"
        else
            test_fail ".env.example does not contain ANTHROPIC_API_KEY"
        fi
    else
        test_fail ".env.example file does not exist"
    fi
}

# Test environment variable guidance function
test_env_file_instructions() {
    test_info "Testing environment file instructions"

    # Capture output from show_env_file_instructions
    local output=$(show_env_file_instructions "GITHUB_REPO_URL" "ANTHROPIC_API_KEY" 2>&1)

    if [[ "$output" =~ "Required environment variables are missing" ]]; then
        test_pass "Instructions show missing variables message"
    else
        test_fail "Instructions do not show missing variables message"
    fi

    if [[ "$output" =~ "cp .env.example .env" ]]; then
        test_pass "Instructions include copy command"
    else
        test_fail "Instructions do not include copy command"
    fi
}

# Main test execution
main() {
    echo ""
    echo -e "${BLUE}🧪 ADWS Setup Auto-Detection Test Suite${NC}"
    echo "=============================================="
    echo ""

    # Source the setup script functions
    test_info "Loading setup script functions..."
    if source_setup_script; then
        test_pass "Setup script functions loaded successfully"
    else
        test_fail "Failed to load setup script functions"
        exit 1
    fi

    echo ""

    # Run all tests
    test_ssh_url_conversion
    echo ""

    test_github_url_validation
    echo ""

    test_repo_info_extraction
    echo ""

    test_github_repo_detection
    echo ""

    test_env_example_exists
    echo ""

    test_env_file_instructions
    echo ""

    # Show test summary
    echo "=============================================="
    echo -e "${BLUE}📊 Test Summary${NC}"
    echo "=============================================="
    echo "Total tests: $TESTS_TOTAL"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    echo ""

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed. Please review the output above.${NC}"
        exit 1
    fi
}

# Check if script is being executed (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi