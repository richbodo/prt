# Bug: Chat Screen JSON Serialization Error in Tool Calling

## Bug Description
When sending a simple query like "How many contacts are in the database?" in the TUI chat screen, instead of receiving a proper LLM response, the user sees:

```
> You: How many contacts are in the database?
Error processing response: the JSON object must be str, bytes or bytearray, not dict
```

This error occurs when the LLM attempts to use tool calling for database queries, but fails due to improper JSON handling of tool call arguments.

## Problem Statement
The LLM tool calling logic in `llm_ollama.py` assumes tool call arguments are always JSON strings that need parsing, but Ollama may return them as already-parsed dictionaries. This causes a `json.loads()` call to fail when passed a dict instead of a string.

## Solution Statement
Fix the JSON handling in the tool calling logic to properly handle both string and dict formats for tool call arguments. Add proper type checking before attempting JSON parsing.

## Steps to Reproduce
1. Run `source ./init.sh` to set up the development environment
2. Launch the TUI with `python -m prt_src`
3. Navigate to the Chat screen (press 'c' from home)
4. Wait for LLM to load and show "READY" status
5. Type "How many contacts are in the database?" in the chat input box
6. Press Enter to send the query
7. Observe the JSON error in the response area

**Expected:** A clear answer like "You have 1810 contacts in your database"
**Actual:** "Error processing response: the JSON object must be str, bytes or bytearray, not dict"

## Root Cause Analysis
The error occurs in `prt_src/llm_ollama.py` at line 1123 in the `chat()` method:

```python
arguments = json.loads(tool_call["function"]["arguments"])
```

When the LLM returns tool calls, `tool_call["function"]["arguments"]` may already be a parsed dictionary instead of a JSON string. Calling `json.loads()` on a dict triggers the error: "the JSON object must be str, bytes or bytearray, not dict".

This is caught by the generic exception handler at line 1171:
```python
except Exception as e:
    return f"Error processing response: {e}"
```

## Relevant Files
Use these files to fix the bug:

- `prt_src/llm_ollama.py` - Contains the faulty JSON parsing logic in the `chat()` method at line 1123
- `prt_src/tui/screens/chat.py` - Chat screen that displays the error message
- `tests/test_llm_ollama.py` - Test file to verify tool calling works properly

### New Files
- `tests/test_chat_tool_calling_json_handling.py` - Test file specifically for JSON handling in tool calls

## Step by Step Tasks

### Step 1: Fix JSON Handling in Tool Calling
- Examine `prt_src/llm_ollama.py` line 1123 where the JSON error occurs
- Replace `json.loads(tool_call["function"]["arguments"])` with type-safe logic
- Check if arguments is already a dict before attempting to parse as JSON
- Handle both string and dict formats gracefully

### Step 2: Add Type Safety to Tool Argument Processing
- Add proper type checking for `tool_call["function"]["arguments"]`
- Implement safe JSON parsing that handles multiple input types
- Add logging to track the actual type received from Ollama
- Ensure backward compatibility with string-based arguments

### Step 3: Improve Error Handling and Logging
- Add more specific error messages for different types of JSON parsing failures
- Log the exact type and content of tool call arguments for debugging
- Ensure that tool calling failures don't break the entire chat flow
- Provide helpful error messages when tool calls fail

### Step 4: Test Tool Calling with Different Argument Formats
- Create tests that simulate both string and dict argument formats
- Test the specific query "How many contacts are in the database?" that triggered the bug
- Verify that other tool calling scenarios work correctly
- Test edge cases like empty arguments, malformed JSON, etc.

### Step 5: Verify Database Query Tools Work Correctly
- Test that the database counting query works once JSON handling is fixed
- Ensure the `execute_sql` tool can properly count contacts
- Verify that other database tools work with the corrected JSON handling
- Test multiple database query scenarios through the chat interface

### Step 6: Add Comprehensive Test Coverage
- Create `tests/test_chat_tool_calling_json_handling.py` with specific JSON handling tests
- Add headless tests using Textual Pilot for the chat screen tool calling
- Test both successful tool calls and error scenarios
- Ensure test coverage for both argument format types (string and dict)

### Step 7: Validate Fix with Original Use Case
- Test the exact scenario from the bug report
- Verify that "How many contacts are in the database?" returns a proper response
- Test other common database queries to ensure broad functionality
- Confirm error messages are helpful when legitimate errors occur

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `source ./init.sh` - Set up development environment
- `python -m prt_src --debug` - Launch TUI with debug data for testing
- Manual test: Send "How many contacts are in the database?" in chat and verify proper response
- `./prt_env/bin/pytest tests/test_llm_ollama.py -v` - Test LLM integration
- `./prt_env/bin/pytest tests/test_chat_tool_calling_json_handling.py -v` - Test new JSON handling
- `./prt_env/bin/pytest -k "chat" -v` - Run all chat-related tests
- `./prt_env/bin/pytest -m integration` - Run integration tests
- `./scripts/run-ci-tests.sh` - Run full CI test suite

## Notes
- This is a classic API integration issue where different response formats aren't handled robustly
- The fix should be minimal and focused on the JSON handling logic
- Proper type checking will prevent similar issues with other tool calls
- The error was confusing because it's caught by a generic exception handler
- Consider adding debug logging to help diagnose future tool calling issues