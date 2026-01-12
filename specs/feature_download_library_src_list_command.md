# Feature: Enhance download_library_src.sh with --list Option

## Feature Description
Add a `--list` option to the `download_library_src.sh` script that provides a comprehensive inventory report of library repositories. This feature will:
1. Display the list of all libraries that should be downloaded (as defined in the script)
2. Show which libraries are already downloaded in the EXTERNAL_DOCS directory
3. Compare the two lists to identify libraries that need to be downloaded
4. Identify any libraries in EXTERNAL_DOCS that are not defined in the download script

This enhancement improves visibility into the documentation library status and helps developers understand which external documentation is available, missing, or extraneous.

## User Story
As a **developer working on PRT**
I want to **quickly see which external library documentation is downloaded and which is missing**
So that **I can ensure I have all necessary documentation available locally and maintain a clean EXTERNAL_DOCS directory**

## Problem Statement
Currently, developers must manually inspect both the `download_library_src.sh` script and the `EXTERNAL_DOCS/` directory to understand:
- Which libraries should be downloaded
- Which libraries are actually present
- Which libraries need to be downloaded
- Whether there are any unexpected/unlisted directories in EXTERNAL_DOCS

This manual process is time-consuming and error-prone. Without a clear inventory, developers may:
- Miss important documentation needed for development
- Be unaware of stale or unused library repositories cluttering the workspace
- Waste time debugging issues that could be solved with available documentation

## Solution Statement
Implement a `--list` flag for the `download_library_src.sh` script that generates a comprehensive inventory report. The solution will:
1. Parse the script itself to extract all repository paths defined for cloning
2. Scan the EXTERNAL_DOCS directory to identify all existing subdirectories
3. Perform a set comparison to categorize libraries into:
   - **Available**: Libraries that are defined and downloaded
   - **Missing**: Libraries that are defined but not yet downloaded
   - **Unlisted**: Directories in EXTERNAL_DOCS not defined in the script
4. Present the information in a clear, human-readable format with color coding for visual clarity

## Relevant Files

### Existing Files
- `download_library_src.sh` - The main script that will be enhanced with the `--list` option. This file already contains:
  - The `TARGET_DIR` variable defining where libraries are stored
  - All `clone_repo` calls defining which libraries should be downloaded
  - The `clone_repo` function that handles git operations

### New Files
None. This feature only modifies the existing `download_library_src.sh` script.

## Implementation Plan

### Phase 1: Foundation
Add command-line argument parsing to the script to support the `--list` flag alongside the existing default behavior. Ensure backward compatibility so the script continues to work normally when called without arguments.

### Phase 2: Core Implementation
Implement the inventory collection and comparison logic:
1. Extract library definitions from the script itself
2. Scan the EXTERNAL_DOCS directory for existing libraries
3. Perform set operations to categorize libraries
4. Format and display the results with clear visual hierarchy

### Phase 3: Integration
Integrate the new functionality seamlessly with the existing script structure, ensuring:
- The script maintains its current behavior when called without `--list`
- Error handling for edge cases (e.g., missing EXTERNAL_DOCS directory)
- Clear documentation in the script comments and help text

## Step by Step Tasks

### Task 1: Add Argument Parsing
- Add a function to parse command-line arguments
- Detect `--list` or `-l` flag
- Add `--help` or `-h` flag to display usage information
- Show usage information if invalid arguments are provided

### Task 2: Implement Library Definition Extraction
- Create a function `get_defined_libraries()` that:
  - Reads the script itself to find all `clone_repo` calls
  - Extracts repository names from the paths (e.g., "typer" from "tiangolo/typer")
  - Returns a sorted list of library names that should be downloaded

### Task 3: Implement EXTERNAL_DOCS Directory Scanner
- Create a function `get_downloaded_libraries()` that:
  - Checks if the EXTERNAL_DOCS directory exists
  - Lists all subdirectories (excluding hidden directories like `.DS_Store` files)
  - Returns a sorted list of library names currently in EXTERNAL_DOCS

### Task 4: Implement Comparison Logic
- Create a function `compare_libraries()` that:
  - Takes the defined and downloaded library lists as input
  - Calculates which libraries are available (in both lists)
  - Calculates which libraries are missing (defined but not downloaded)
  - Calculates which libraries are unlisted (downloaded but not defined)
  - Returns these three categorized lists

### Task 5: Implement Display Function
- Create a function `display_library_status()` that:
  - Prints a header with summary statistics
  - Displays available libraries with a ✅ indicator
  - Displays missing libraries with a ❌ indicator
  - Displays unlisted libraries with a ⚠️  indicator
  - Uses clear section headers and formatting for readability
  - Optionally uses color codes if terminal supports it (green/red/yellow)

### Task 6: Wire Up the --list Functionality
- Modify the main script logic to:
  - Check if `--list` flag is provided at the start
  - If provided, call the inventory functions and exit
  - Otherwise, proceed with the normal clone behavior
  - Ensure the script exits with appropriate exit codes

### Task 7: Add Documentation
- Update the script header comments to document the `--list` option
- Add inline comments explaining the new functions
- Include usage examples in the help text

### Task 8: Test the Implementation
- Test `./download_library_src.sh --list` with various scenarios:
  - When EXTERNAL_DOCS doesn't exist (fresh checkout)
  - When some libraries are downloaded
  - When all libraries are downloaded
  - When there are unlisted directories in EXTERNAL_DOCS
- Test that the normal clone behavior still works: `./download_library_src.sh`
- Test help display: `./download_library_src.sh --help`
- Verify output formatting is clear and readable

### Task 9: Run Validation Commands
Execute all validation commands listed below to ensure the feature works correctly with zero regressions.

## Testing Strategy

### Unit Tests
This is a bash script enhancement, so formal unit tests are not applicable. However, functional testing will cover:
- **Argument parsing**: Verify `--list`, `-l`, `--help`, `-h` flags work correctly
- **Library extraction**: Verify all `clone_repo` calls are correctly identified
- **Directory scanning**: Verify all subdirectories in EXTERNAL_DOCS are found
- **Comparison logic**: Verify correct categorization of available/missing/unlisted libraries
- **Display formatting**: Verify output is readable and contains all expected information

### Edge Cases
- **Empty EXTERNAL_DOCS**: Script should report all libraries as missing
- **EXTERNAL_DOCS doesn't exist**: Script should handle gracefully without errors
- **Hidden files/directories**: `.DS_Store` and `.git` should be excluded from listings
- **All libraries downloaded**: Should show all libraries as available, none missing
- **Extra directories**: Should correctly identify unlisted directories
- **No arguments**: Script should perform normal clone operation (backward compatibility)
- **Invalid arguments**: Script should show usage information

## Acceptance Criteria
1. Running `./download_library_src.sh --list` displays a comprehensive inventory report
2. The report shows three sections: Available, Missing, and Unlisted libraries
3. The report includes a summary count for each category
4. The output is clearly formatted with visual indicators (✅, ❌, ⚠️)
5. The script correctly identifies all 19 libraries defined in `clone_repo` calls
6. The script correctly scans the EXTERNAL_DOCS directory for existing libraries
7. The script handles edge cases gracefully (missing directory, no libraries, etc.)
8. Running `./download_library_src.sh` without arguments maintains existing clone behavior
9. Running `./download_library_src.sh --help` displays usage information
10. The implementation does not break any existing functionality

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
# Test 1: Display help information
./download_library_src.sh --help
# Expected: Shows usage information and exits

# Test 2: Run list command when EXTERNAL_DOCS is empty
rm -rf EXTERNAL_DOCS
./download_library_src.sh --list
# Expected: Shows all libraries as "Missing", none as "Available"

# Test 3: Download one library and verify list
mkdir -p EXTERNAL_DOCS
cd EXTERNAL_DOCS
git clone --depth 1 https://github.com/tiangolo/typer.git
cd ..
./download_library_src.sh --list
# Expected: Shows "typer" as Available, other libraries as Missing

# Test 4: Create an unlisted directory and verify detection
mkdir -p EXTERNAL_DOCS/unknown-library
./download_library_src.sh --list
# Expected: Shows "unknown-library" in Unlisted section

# Test 5: Verify normal clone operation still works
./download_library_src.sh
# Expected: Clones missing repositories, skips existing ones

# Test 6: Verify list after full download
./download_library_src.sh --list
# Expected: Most/all libraries show as Available

# Test 7: Verify output format is readable
./download_library_src.sh --list | head -20
# Expected: Clear headers, visual indicators, organized sections

# Test 8: Verify script exits with proper codes
./download_library_src.sh --list && echo "Exit code: $?"
# Expected: Exit code 0

# Test 9: Test invalid argument handling
./download_library_src.sh --invalid-flag
# Expected: Shows usage/help message

# Test 10: Verify backward compatibility (no arguments)
./download_library_src.sh
# Expected: Runs normal clone operation
```

## Notes
- The script should use POSIX-compatible bash features for maximum portability
- Color codes should be optional and degrade gracefully on terminals that don't support colors
- The comparison logic should be case-insensitive to handle potential naming differences
- Consider adding counts to section headers (e.g., "Available Libraries (5)") for quick scanning
- The script extracts library names from repository paths by taking the last component (e.g., "typer" from "tiangolo/typer")
- Hidden directories (starting with `.`) and files like `.DS_Store` should be filtered out when scanning EXTERNAL_DOCS
- The script should maintain the existing behavior: it creates EXTERNAL_DOCS if it doesn't exist during clone operations, but should only report status (not create) during `--list` operations
