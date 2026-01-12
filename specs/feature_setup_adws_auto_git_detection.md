# Feature: Automatic GitHub Repository URL Detection in setup_adws.sh

## Feature Description
Enhance the `setup_adws.sh` script to automatically detect the GitHub repository URL from the local git configuration, eliminating the need for manual input in most cases. When environment variables cannot be found or detected, the script should provide clear guidance directing users to add the required variables to the `.env` file with helpful instructions and examples.

## User Story
As a developer setting up the ADWS (AI Developer Workflow) system
I want the setup script to automatically detect my GitHub repository URL from my local git configuration
So that I don't need to manually enter information that can be automatically determined, making the setup process faster and less error-prone

## Problem Statement
The current `setup_adws.sh` script requires users to manually enter the GitHub repository URL during interactive setup, even though this information is typically available in the local git configuration. When environment variables are missing, the script doesn't provide clear guidance on how to add them to the `.env` file, leading to configuration errors and setup friction.

## Solution Statement
Implement automatic GitHub repository URL detection by extracting the information from git remote configuration, converting SSH URLs to HTTPS format as needed. When required environment variables cannot be found or auto-detected, provide explicit instructions to users on creating and populating the `.env` file with proper examples and validation.

## Relevant Files
Use these files to implement the feature:

- **`setup_adws.sh`** - Main setup script that needs enhancement for auto-detection and better error guidance
  - Currently prompts for GitHub repository URL manually
  - Needs new functions to detect git remote information
  - Needs improved error messaging for missing environment variables

- **`.env.example`** - Template file that users should copy to create their `.env` file
  - Provides examples and documentation for required variables
  - Referenced in error messages to guide users

### New Files
- **`tests/test_setup_adws.sh`** - Test script to validate the auto-detection functionality and error handling

## Implementation Plan
### Phase 1: Foundation
Add git repository URL auto-detection functionality to the setup script, including helper functions to extract and validate repository information from local git configuration.

### Phase 2: Core Implementation
Implement the main auto-detection logic that attempts to determine the GitHub repository URL before falling back to interactive prompts, with proper validation and error handling.

### Phase 3: Integration
Enhance the error handling and user guidance when environment variables cannot be detected or are missing, providing clear instructions for manual `.env` file setup.

## Step by Step Tasks

### Step 1: Add Git Repository Detection Functions
- Add `detect_github_repo_url()` function to extract repository URL from git remote
- Add `convert_ssh_to_https()` function to convert SSH URLs (git@github.com:user/repo.git) to HTTPS format
- Add `extract_repo_info()` function to parse and validate repository information
- Add comprehensive error handling for cases where git remote is not available

### Step 2: Implement Auto-Detection Logic
- Modify the main setup flow to attempt auto-detection before prompting user
- Update the `prompt_for_var()` function to accept auto-detected values as defaults
- Add validation to ensure auto-detected URLs match expected GitHub format
- Add fallback logic when auto-detection fails or returns invalid URLs

### Step 3: Enhanced Environment Variable Guidance
- Improve error messages when required environment variables are completely missing
- Add `show_env_file_instructions()` function that provides step-by-step guidance
- Include examples from `.env.example` in error messages
- Add validation that `.env.example` exists before referencing it

### Step 4: Update Configuration Validation
- Enhance `check_config()` function to report auto-detection status
- Add informational messages showing detected vs. configured values
- Improve error messages to distinguish between detection failures and validation failures

### Step 5: Comprehensive Testing
- Create test script `tests/test_setup_adws.sh` to validate auto-detection functionality
- Test with various git remote configurations (SSH, HTTPS, multiple remotes)
- Test error scenarios (no git repo, no remotes, invalid remotes)
- Validate that existing functionality remains intact

### Step 6: Documentation and Help Updates
- Update help text to mention auto-detection capabilities
- Add examples of what happens when auto-detection succeeds vs. fails
- Document the priority order: existing env vars > auto-detection > user prompts

### Step 7: Validation Testing
- Run comprehensive tests to ensure zero regressions in existing functionality
- Test the complete setup flow with and without existing environment variables
- Validate error handling and user guidance improvements
- Ensure all validation commands execute successfully

## Testing Strategy
### Unit Tests
- Test `detect_github_repo_url()` with various git remote configurations
- Test `convert_ssh_to_https()` URL conversion with edge cases
- Test `extract_repo_info()` parsing and validation logic
- Test error handling when git commands fail or return unexpected output

### Integration Tests
- Test complete setup flow with auto-detection enabled
- Test fallback behavior when auto-detection fails
- Test interaction between auto-detection and existing environment variables
- Test user experience when environment variables are completely missing

### Edge Cases
- No git repository initialized
- Multiple git remotes with different URLs
- Invalid or non-GitHub git remotes
- SSH URLs with non-standard formats
- Corrupted or missing `.env.example` file
- Git commands that fail or timeout

## Acceptance Criteria
- Script automatically detects GitHub repository URL from git remote when available
- SSH URLs are correctly converted to HTTPS format for ADWS compatibility
- Auto-detected URLs are validated before use and invalid ones are rejected
- When auto-detection fails, user is prompted with clear instructions
- When environment variables are missing, script provides explicit guidance to create `.env` file
- Error messages reference `.env.example` and provide copy commands
- Existing functionality remains unchanged for users who already have environment variables configured
- Script handles edge cases gracefully (no git repo, multiple remotes, etc.)
- Help documentation reflects new auto-detection capabilities

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `source ./setup_adws.sh --help` - Verify help text includes auto-detection information
- `source ./setup_adws.sh --check` - Check existing configuration validation works unchanged
- `bash tests/test_setup_adws.sh` - Run comprehensive test suite for auto-detection functionality
- `git remote -v` - Verify git remote configuration for testing
- `rm .env 2>/dev/null; source ./setup_adws.sh` - Test complete setup flow with auto-detection from clean state
- `source ./setup_adws.sh --reset` - Verify reset functionality works with auto-detection
- `ls -la .env.example` - Ensure template file exists for error message references

## Notes
- The auto-detection feature should be non-intrusive and not change the behavior for users who already have properly configured environment variables
- SSH URL conversion is critical since many developers use SSH for git operations but ADWS requires HTTPS URLs
- Error messages should be helpful and actionable, providing specific commands users can run to resolve issues
- Consider adding a `--no-auto-detect` flag for users who want to force manual entry
- The feature should gracefully handle corporate environments where git remotes might use different hosting services
- Future consideration: Support for GitLab or other git hosting services beyond GitHub