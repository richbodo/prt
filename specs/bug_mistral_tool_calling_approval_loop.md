# Bug: Mistral Tool Calling Approval Loop

## Bug Description
When using the Mistral LLM model for chat with tool calling enabled, the model repeatedly asks for user permission to execute tools instead of actually executing them. After the user approves tool execution with responses like "Yup. go ahead and run it.", Mistral continues to ask for permission again with identical messages, creating an infinite loop where tools are never executed.

**Symptoms:**
- Mistral model asks "I can run: `search_contacts("friends")`. Should I execute it?"
- User responds with approval ("Yup. go ahead and run it.")
- Mistral repeats the exact same permission request instead of executing the tool
- No tool execution occurs despite user approval
- Loop continues indefinitely

**Expected Behavior:**
- Mistral asks for permission to run tool (optional)
- User approves tool execution
- Tool is executed automatically
- Results are returned to user
- Conversation continues normally

**Actual Behavior:**
- Mistral asks for permission
- User approves
- Mistral asks for permission again (infinite loop)
- No tools are ever executed

## Problem Statement
There is a fundamental mismatch between the system prompt guidance that instructs the LLM to "ask user first" for tool execution and the automatic tool execution architecture in the codebase. Mistral's strict instruction-following behavior causes it to ask for confirmation in its response text, but the system automatically executes detected tool calls regardless of user approval, creating a confusion loop.

## Solution Statement
Implement a proper user approval mechanism for tool execution that:
1. Presents planned tool calls to the user before execution
2. Waits for explicit user approval
3. Only executes tools after confirmed approval
4. Handles rejection and modification of tool calls
5. Updates system prompts to align with the approval architecture

## Steps to Reproduce
1. Ensure Mistral model is installed and available via Ollama
2. Run: `python -m prt_src --cli --model mistral-7b-instruct --chat "find friends"`
3. Observe Mistral response asking for permission: "I can run: `search_contacts("friends")`. Should I execute it?"
4. Respond with approval: "Yup. go ahead and run it."
5. Observe Mistral repeats the exact same permission request
6. Tool is never executed despite user approval

## Root Cause Analysis
**Primary Cause:** Architecture mismatch between system prompt and code execution

1. **System Prompt Conflict:** The system prompt in `llm_prompts.py` instructs LLMs to "ask user first" for tool execution, but the code in `llm_base.py` automatically executes all detected tool calls without user interaction.

2. **Mistral Instruction Following:** Mistral's v0.3 instruction-tuned behavior causes it to strictly follow the "ask user first" guidance, generating both tool calls AND confirmation request text in its response.

3. **Automatic Execution:** The `BaseLLM.chat()` method in `llm_base.py:92-103` automatically extracts and executes tool calls without checking for user approval.

4. **Response Loop:** When Mistral's response contains tool calls + confirmation request:
   - System extracts and executes tool calls automatically
   - Confirmation request text is added to conversation history
   - User approval becomes a new message in the next iteration
   - Mistral treats this as a new request and asks for permission again

5. **No Approval Architecture:** The codebase has no mechanism to:
   - Present tool calls to users before execution
   - Wait for user approval
   - Handle approval/rejection decisions
   - Distinguish between approved and unapproved tool execution

## Relevant Files
Use these files to fix the bug:

- `prt_src/llm_base.py:92-103` - Contains automatic tool execution logic that needs approval mechanism
- `prt_src/llm_ollama.py:1302-1346` - Tool call extraction and formatting for Mistral
- `prt_src/llm_prompts/database_chat_system_prompt.txt:54-62` - System prompt that instructs "ask user first"
- `prt_src/llm_tools.py` - Tool registry that needs approval annotations
- `prt_src/cli.py:chat_mode()` - CLI chat interface where approval UI needs to be implemented
- `tests/integration/test_mistral_tool_calling.py` - Test file that needs real approval workflow tests

### New Files
- `prt_src/llm_approval.py` - New approval mechanism for tool execution
- `tests/integration/test_tool_approval_workflow.py` - Integration tests for approval workflow

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Research and Reproduce Bug
- Verify current Mistral tool calling behavior by running the reproduction steps
- Document exact response patterns and loop behavior
- Confirm the automatic tool execution in `llm_base.py` is working as designed
- Identify specific points where approval mechanism should be inserted

### Create Tool Approval Architecture
- Design and implement `prt_src/llm_approval.py` with approval mechanism
- Add `ToolApproval` class to handle presentation of tool calls to user
- Add approval decision handling (approve, reject, modify)
- Add integration points for different interfaces (CLI, TUI)
- Add safety checks and validation for tool approval decisions

### Integrate Approval Mechanism into BaseLLM
- Modify `prt_src/llm_base.py` to use approval mechanism before tool execution
- Add approval check in `chat()` method before calling `_call_tool()`
- Handle approval responses and continue conversation appropriately
- Preserve existing automatic execution for non-interactive scenarios
- Add configuration option to enable/disable approval requirement

### Update System Prompts
- Modify `prt_src/llm_prompts/database_chat_system_prompt.txt` to align with approval architecture
- Remove conflicting "ask user first" guidance that creates the loop
- Add clear instructions for tool calling behavior with approval system
- Test prompt changes with Mistral to ensure proper tool call generation

### Implement CLI Approval Interface
- Add approval presentation logic to `prt_src/cli.py` chat mode
- Display planned tool calls to user in readable format
- Prompt for user approval decision (approve/reject/modify)
- Handle user responses and communicate decisions back to approval mechanism
- Add proper error handling for approval timeout or invalid responses

### Write Comprehensive Tests
- Create `tests/integration/test_tool_approval_workflow.py` for approval mechanism testing
- Add real Mistral tool calling tests (not mocked) to verify loop is fixed
- Test approval, rejection, and modification scenarios
- Add tests for automatic execution when approval is disabled
- Update existing `test_mistral_tool_calling.py` with approval workflow validation

### Fix Mistral-Specific Implementation
- Review `prt_src/llm_ollama.py` Mistral-specific configurations
- Ensure tool call extraction works properly with approval mechanism
- Verify temperature optimization doesn't interfere with approval workflow
- Test tool call ID generation compatibility with approval system

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

**Setup and Environment:**
- `source ./init.sh` - Setup development environment
- `python -m prt_src --models` - Verify Mistral model availability

**Reproduce Original Bug (Should FAIL before fix):**
- `python -m prt_src --cli --model mistral-7b-instruct --chat "find friends"` - Reproduce approval loop bug

**Run All Tests:**
- `./prt_env/bin/pytest tests/integration/test_mistral_tool_calling.py -v` - Run Mistral-specific tests
- `./prt_env/bin/pytest tests/integration/test_tool_approval_workflow.py -v` - Run new approval tests
- `./prt_env/bin/pytest tests/ -m integration -v` - Run all integration tests
- `./scripts/run-ci-tests.sh` - Run full CI test suite

**Validate Fix Works (Should PASS after fix):**
- `python -m prt_src --cli --model mistral-7b-instruct --chat "find friends"` - Test approval workflow works
- `python -m prt_src --cli --model gpt-oss:20b --chat "find friends"` - Verify other models still work
- `python -m prt_src --debug --cli --model mistral-7b-instruct --chat "list all contacts"` - Test with debug data

**Regression Testing:**
- `./prt_env/bin/pytest tests/test_llm_* -v` - Run all LLM-related tests
- `python -m prt_src --cli chat` - Test CLI chat mode generally
- `python -m prt_src` - Test TUI still works with changes

## Notes
- This bug affects ONLY Mistral models due to their strict instruction-following behavior
- Other models (like gpt-oss:20b) work correctly because they don't ask for confirmation
- The approval mechanism should be optional and configurable to maintain backward compatibility
- Consider adding approval requirement configuration to `prt_config.json`
- The system prompt changes should be tested with multiple LLM models to ensure compatibility
- Real Ollama integration tests require Mistral model to be installed locally
- This fix addresses a fundamental UX issue where users expect tools to execute after approval