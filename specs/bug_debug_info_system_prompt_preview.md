# Bug: Debug Info System Prompt Preview Too Short

## Bug Description
The `--prt-debug-info` command shows a truncated system prompt preview that cuts off at 500 characters, making it appear "way too short to possibly work". Users cannot verify that the system prompt contains tool descriptions and other important content. While the system prompt is actually working correctly (19803 characters), the debug display only shows the first 500 characters, cutting off before the critical tools section that starts around character ~970.

Additionally, some unit tests for the debug info feature are failing due to mocking issues and assertion problems.

## Problem Statement
1. The debug info system prompt preview is too short (500 chars) to show the important tool descriptions section
2. Users cannot verify that the system prompt is properly constructed with all tools and schema information
3. Several unit tests are failing in the debug info module

## Solution Statement
1. Increase the system prompt preview length to show more meaningful content including the tools section
2. Add a configurable preview length with a reasonable default
3. Fix the failing unit tests related to debug info functionality
4. Ensure the preview shows enough content to verify tool descriptions are included

## Steps to Reproduce
1. Run `python -m prt_src --prt-debug-info`
2. Observe the "📄 SYSTEM PROMPT" section
3. Note that the preview shows only ~500 characters and cuts off with "..." before the tools section
4. Run `./prt_env/bin/pytest tests/unit/test_debug_info.py -v` to see failing tests

## Root Cause Analysis
The issue is in `prt_src/debug_info.py` at line 258 where the preview is hardcoded to 500 characters:

```python
prompt_info["prompt_preview"] = (
    system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt
)
```

The system prompt structure shows that:
- First ~500 chars: Basic PRT description and role
- Around char 970+: Critical tools section with `## AVAILABLE TOOLS` and tool descriptions
- The current preview cuts off before users can verify tools are included

Additional issues:
1. Unit test failures due to mocking problems with `__truediv__` operator and connectivity test assertions
2. Timeout test expecting specific exception format that changed

## Relevant Files
- `prt_src/debug_info.py` - Contains the `collect_system_prompt()` function that creates the 500-char preview (line 258)
- `tests/unit/test_debug_info.py` - Contains failing unit tests that need fixes
- `prt_src/llm_ollama.py` - Contains `_create_system_prompt()` method that properly builds the full system prompt with tools

### Key Functions:
- `collect_system_prompt()` in `debug_info.py` - Creates the truncated preview
- `format_debug_output()` in `debug_info.py` - Formats the debug display
- Unit tests in `test_debug_info.py` - Need fixing for mocking and assertions

## Step by Step Tasks

### 1. Fix System Prompt Preview Length
- Update `collect_system_prompt()` to show more meaningful content
- Increase preview length to ~1500 characters to include the tools section
- Add configuration option for preview length
- Ensure preview shows "## AVAILABLE TOOLS" section

### 2. Improve Preview Content Selection
- Instead of just taking first N characters, show structured sections
- Include: Role description + Tools section + truncation indicator if needed
- Add preview sections: "Basic description..." + "Tools available..." + "..."

### 3. Fix Failing Unit Tests
- Fix `test_collect_system_environment_ollama_timeout` - Update assertion for timeout message format
- Fix `test_collect_llm_info_success` - Fix connectivity test assertion logic
- Fix `test_collect_config_info_success` - Fix `__truediv__` mocking issue for Path operations

### 4. Add Test for Enhanced Preview
- Add test to verify system prompt preview includes tools section
- Verify preview length is sufficient to show meaningful content
- Test configuration of preview length

### 5. Update Documentation
- Update any debug info documentation to reflect improved preview
- Document the preview length configuration if added

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `python -m prt_src --prt-debug-info` - Verify system prompt preview now shows tools section
- `./prt_env/bin/pytest tests/unit/test_debug_info.py -v` - All unit tests should pass
- `./prt_env/bin/pytest tests/integration/test_debug_info_command.py -v` - All integration tests should pass
- `./prt_env/bin/pytest tests/ -k "debug_info" -v` - All debug info related tests should pass
- `./prt_env/bin/python -c "from prt_src.debug_info import collect_system_prompt; result = collect_system_prompt(); print(f'Preview length: {len(result[\"prompt_preview\"])}')"` - Verify preview is longer than 500 chars
- `./prt_env/bin/python -c "from prt_src.debug_info import collect_system_prompt; result = collect_system_prompt(); print('TOOLS' in result['prompt_preview'])"` - Verify tools section is visible in preview

## Notes
- The system prompt is actually working correctly (19803 characters with full tools) - this is just a display issue in debug output
- The bug affects user confidence in the system since they can't verify the prompt contains tools
- The fix should balance showing meaningful content without making debug output too long
- Consider making the preview length configurable for advanced users who want to see more/less
- Unit test fixes should use proper mocking patterns for Path operations and exception handling