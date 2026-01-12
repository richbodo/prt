# Bug: ADWS Setup Script Corrupts .env File with Interactive Prompts

## Bug Description
The `setup_adws.sh` script is writing interactive user prompts and terminal output directly into the `.env` file instead of writing only the environment variable assignments. This results in a malformed `.env` file that cannot be properly sourced and causes shell errors. The file contains prompts like "📝 GitHub repository URL (e.g., https://github.com/owner/repo)", user interaction text like "Current value:", and ANSI color codes, rather than the expected `KEY=value` format.

When the script attempts to load this corrupted `.env` file using `source "$ENV_FILE"`, it fails with numerous shell errors like "command not found", "unknown file attribute", and "bad pattern" errors. This prevents the environment variables from being loaded correctly, causing the script to report that required variables like `GITHUB_REPO_URL` and `ANTHROPIC_API_KEY` are not set, even when they are present in the file.

## Problem Statement
The root cause is in the `prompt_for_var()` function which writes user interaction prompts to stdout, and the main setup flow uses command substitution `new_repo_url=$(prompt_for_var ...)` which captures ALL stdout output including the prompts, not just the intended return value. This captured output (containing prompts, messages, and formatting) is then assigned to environment variables and written to the `.env` file by `save_env_file()`.

## Solution Statement
Fix the `prompt_for_var()` function to separate user interaction output (which should go to stderr or /dev/tty) from the return value (which should go to stdout for capture). The function should only echo the final variable value to stdout, while all prompts, messages, and user interaction should be directed elsewhere to avoid being captured by command substitution.

## Steps to Reproduce
1. Run `source ./setup_adws.sh` in the project root
2. Follow the interactive prompts to enter values for `GITHUB_REPO_URL` and `ANTHROPIC_API_KEY`
3. Let the script complete and save the configuration
4. Examine the `.env` file with `cat .env` - it will contain interactive prompts instead of proper environment variable assignments
5. Run `source ./setup_adws.sh --check` to see the corruption causes shell errors and variables are not recognized

## Root Cause Analysis
The issue occurs in the `prompt_for_var()` function at lines 348-375 in `setup_adws.sh`. The function writes user prompts to stdout:
- Line 348: `echo ""`
- Line 349: `echo "📝 $description"`
- Line 354/356: `echo "Current value: ..."`
- Line 362: `echo "Auto-detected value: ..."`
- Line 372: `echo "Press Enter to use default value..."`
- Line 375: `echo -n "$var_name: "`

When the main setup flow calls `new_repo_url=$(prompt_for_var ...)`, the command substitution captures ALL of this stdout output, not just the intended return value. This multi-line captured output is then assigned to `$GITHUB_REPO_URL` and written to the `.env` file by the `save_env_file()` function, resulting in a malformed configuration file.

## Relevant Files
Use these files to fix the bug:

- **`setup_adws.sh`** - Contains the buggy `prompt_for_var()` function that writes prompts to stdout instead of separating user interaction from return values
  - Lines 340-400: `prompt_for_var()` function needs output redirection fix
  - Lines 402-438: `save_env_file()` function works correctly but receives corrupted input
  - Lines 549-580: Main setup flow using command substitution that captures corrupted output

- **`.env`** - Corrupted environment file that needs to be restored to proper format
  - Currently contains interactive prompts and terminal output instead of `KEY=value` pairs
  - Must be restored to valid shell environment variable format

- **`.env.example`** - Template file showing correct format for environment variables
  - Used as reference for proper `.env` file structure

### New Files
- **`tests/test_setup_adws_env_corruption.sh`** - Test script to validate the bug is fixed and prevent regressions

## Step by Step Tasks

### Step 1: Fix the prompt_for_var function output redirection
- Redirect all user interaction output (prompts, messages) to stderr or /dev/tty instead of stdout
- Ensure only the final variable value is written to stdout for command substitution capture
- Test the function in isolation to verify it only outputs the intended value

### Step 2: Restore the corrupted .env file
- Create a clean `.env` file by copying from `.env.example`
- Set proper values for `GITHUB_REPO_URL` and `ANTHROPIC_API_KEY` based on the intended values from the corrupted file
- Verify the restored file can be properly sourced without errors

### Step 3: Test the fix end-to-end
- Run the complete setup flow to ensure the fixed function creates a proper `.env` file
- Verify the generated `.env` file contains only valid `KEY=value` assignments
- Confirm that `source ./setup_adws.sh --check` recognizes the environment variables correctly

### Step 4: Create regression test
- Write a comprehensive test script that validates the `.env` file format after setup
- Test that the file contains only valid shell variable assignments
- Ensure the test can be run in CI to prevent future regressions

### Step 5: Validate with all commands
- Run all validation commands to ensure zero regressions
- Test both interactive setup and configuration checking
- Verify the auto-detection features still work correctly

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `cat .env` - Before fix: shows corrupted file with prompts. After fix: shows clean KEY=value pairs
- `source ./setup_adws.sh --check` - Before fix: shell errors and variables not recognized. After fix: clean validation
- `bash -n .env` - Test .env file syntax validity (should have no output if valid)
- `source .env && echo "GITHUB_REPO_URL=$GITHUB_REPO_URL"` - Test that variables load correctly
- `source ./setup_adws.sh --help` - Verify help functionality remains intact
- `bash tests/test_setup_adws_env_corruption.sh` - Run regression test to prevent future corruption
- `rm -f .env && source ./setup_adws.sh` - Test complete setup flow creates clean .env file
- `source ./setup_adws.sh --reset` - Test reset functionality with fixed output redirection

## Notes
- The fix requires careful attention to output redirection in bash - user interaction should go to stderr (`>&2`) or directly to the terminal (`>/dev/tty`) while only the return value goes to stdout
- The auto-detection feature added recently should continue working after the fix
- Consider using `printf` instead of `echo` for more predictable behavior across different shells
- The bug affects all interactive variables, not just GITHUB_REPO_URL and ANTHROPIC_API_KEY
- This is a critical bug that completely breaks the setup script's core functionality