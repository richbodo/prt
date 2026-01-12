# Find Plan File

Based on the variables and `Previous Step Output` below, follow the `Instructions` to find the path to the plan file that was just created.

## Variables
issue_number: $1
adw_id: $2
previous_output: $3

## Instructions

- The previous step created a plan file. Find the exact file path.
- The plan filename follows the pattern: `issue-{issue_number}-adw-{adw_id}-sdlc_planner-{descriptive-name}.md`
- You can use these approaches to find it:
  - First, try: `ls specs/issue-{issue_number}-adw-{adw_id}-sdlc_planner-*.md`
  - Check git status for new untracked files matching the pattern
  - Use `find specs -name "issue-{issue_number}-adw-{adw_id}-sdlc_planner-*.md" -type f`
  - Parse the previous output which should mention where the plan was saved
- Return ONLY the file path (e.g., "specs/issue-7-adw-abc123-sdlc_planner-update-readme.md") or "0" if not found.
- Do not include any explanation, just the path or "0" if not found.

## Previous Step Output

Use the `previous_output` variable content to help locate the file if it mentions the path.