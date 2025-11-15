# Bug: Mistral Ollama Communication Failure

## Bug Description
The Mistral model (`mistral:7b-instruct`) fails to communicate with Ollama when invoked via the CLI, returning a 404 error on the `/api/chat` endpoint despite working correctly for other models like `gpt-oss:20b`. The error manifests when running:
```bash
python -m prt_src --cli --model mistral7b-instruct --chat "hello"
```

**Error Output:**
```
Starting LLM chat mode...
Using model: mistral7b-instruct
🤖 LLM Chat Mode
Type 'quit' to exit, 'clear' to clear history, 'help' for assistance
==================================================

You: hello

Assistant
Thinking...
Error communicating with Ollama: 404 Client Error: Not Found for url: http://localhost:11434/api/chat
```

**Expected Behavior:** Should successfully communicate with Ollama and return a chat response, similar to how `gpt-oss:20b` works.

**Actual Behavior:** Returns 404 error on `/api/chat` endpoint, preventing any chat functionality.

## Problem Statement
The bug has two potential root causes:
1. **Model Name Resolution Issue**: User input `mistral7b-instruct` might not resolve correctly to the canonical model name `mistral:7b-instruct`
2. **Ollama Model Availability**: The `mistral:7b-instruct` model might not be properly installed or available in the local Ollama instance

The architecture is sound - all models use the same Ollama communication code and URL construction (`/api/chat`), but the model resolution or availability is failing specifically for Mistral.

## Solution Statement
Implement comprehensive model validation and improved error handling to:
1. Validate model name resolution from aliases to canonical names
2. Check actual model availability in Ollama before attempting communication
3. Provide clear error messages to guide users toward resolution
4. Ensure consistent model name handling across CLI and TUI interfaces

## Steps to Reproduce
1. Ensure Ollama is running: `brew services start ollama` (macOS) or `systemctl start ollama` (Linux)
2. Verify base connectivity: `curl http://localhost:11434/api/tags` should return JSON
3. Run the failing command: `python -m prt_src --cli --model mistral7b-instruct --chat "hello"`
4. Observe 404 error on `/api/chat` endpoint

## Root Cause Analysis
After comprehensive codebase analysis, the issue stems from **model name resolution and availability validation gaps**:

1. **Model Resolution Chain**: User input `mistral7b-instruct` → Model Registry → Ollama API
   - The `llm_model_registry.py` attempts to resolve user aliases via Ollama's `/api/tags` endpoint
   - If the model `mistral:7b-instruct` is not installed in Ollama, resolution fails silently
   - The system then attempts to use the unresolved alias directly, causing 404 errors

2. **Missing Pre-flight Validation**: The `llm_ollama.py` code assumes the model exists and directly attempts `/api/chat`
   - No explicit model availability check before API calls
   - 404 errors are generic HTTP exceptions, not model-specific validation errors

3. **Architecture is Sound**: The URL construction, API endpoint usage, and tool calling format are identical for all models
   - `gpt-oss:20b` works because it's typically installed and properly resolved
   - `mistral:7b-instruct` fails due to availability, not communication architecture

## Relevant Files

**Primary Files for Investigation:**
- `prt_src/llm_factory.py:56-140` - Model resolution logic that converts aliases to canonical names
- `prt_src/llm_model_registry.py:338-380` - Alias resolution and model discovery via Ollama API
- `prt_src/llm_ollama.py:1290-1296` - URL construction and HTTP communication with Ollama
- `prt_src/llm_ollama.py:1413-1430` - Error handling for HTTP exceptions

**Supporting Files for Context:**
- `prt_src/llm_supported_models.py:70-86` - Mistral model metadata and official support status
- `prt_src/cli.py:2905-2910` - CLI argument parsing for `--model` parameter
- `prt_src/cli.py:2968-2991` - Chat mode initialization and error handling

### New Files
None required - this is a validation and error handling enhancement to existing architecture.

## Step by Step Tasks

### 1. Reproduce and Validate the Bug
- Test the exact command that's failing: `python -m prt_src --cli --model mistral7b-instruct --chat "hello"`
- Verify Ollama service is running and accessible: `curl http://localhost:11434/api/tags`
- Check if `mistral:7b-instruct` model is installed: `ollama list | grep mistral`
- Test with working model for comparison: `python -m prt_src --cli --model gpt-oss-20b --chat "hello"`

### 2. Enhance Model Availability Validation
- Modify `llm_factory.py:resolve_model_alias()` to add explicit model availability validation
- Add logging to show the complete model resolution chain: input → resolved name → availability check
- Ensure model existence is verified before creating LLM instances
- Add specific error messages for model not found vs Ollama service unavailable

### 3. Improve Error Handling in Ollama Communication
- Enhance `llm_ollama.py` error handling to distinguish between:
  - HTTP 404 due to model not found vs endpoint issues
  - Network connectivity problems vs service availability
  - Model-specific errors vs general Ollama failures
- Add pre-flight model validation before attempting `/api/chat` calls

### 4. Add Comprehensive Model Validation Tests
- Create test cases for model resolution with various alias formats
- Test behavior when models are not installed in Ollama
- Verify error messages guide users toward correct resolution steps
- Ensure consistent behavior between CLI `--model` parameter and TUI model selection

### 5. Validate Against Documentation
- Ensure model names in documentation match supported aliases
- Verify installation instructions for Mistral model are accurate
- Update error messages to reference correct model installation commands

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

**Pre-fix Validation (Reproduce Bug):**
- `curl http://localhost:11434/api/tags` - Verify Ollama is accessible
- `ollama list` - Check which models are currently installed
- `python -m prt_src --cli --model mistral7b-instruct --chat "hello"` - Reproduce the 404 error
- `python -m prt_src --cli --model gpt-oss-20b --chat "hello"` - Verify working model still works

**Post-fix Validation (Verify Resolution):**
- `python -m prt_src --cli --model mistral7b-instruct --chat "hello"` - Should now show clear error about model availability
- `ollama pull mistral:7b-instruct` - Install the missing model (if needed)
- `python -m prt_src --cli --model mistral7b-instruct --chat "hello"` - Should work after installation
- `python -m prt_src --cli --model nonexistent-model --chat "hello"` - Should show helpful error message
- `python -m prt_src.cli list-models` - Should show model support status clearly

**Regression Testing:**
- `./prt_env/bin/pytest tests/ -k "llm" -v` - Run all LLM-related tests
- `./prt_env/bin/pytest tests/integration/test_mistral_tool_calling.py -v` - Run Mistral-specific tests
- `./prt_env/bin/pytest tests/test_llm_model_registry.py -v` - Test model resolution logic
- `python -m prt_src.tui --model mistral-7b-instruct` - Test TUI integration
- `python -m prt_src.tui --model gpt-oss-20b` - Verify TUI still works with known models

## Notes
- This is not a fundamental architecture issue - the Ollama communication code is shared and working
- The bug likely manifests as a model availability/installation issue disguised as an API communication failure
- Focus on improving error messages and validation rather than changing core communication logic
- Consider that users may input various alias formats (`mistral7b-instruct`, `mistral-7b-instruct`, `mistral:7b-instruct`) and all should resolve correctly
- The 404 error is misleading - it suggests API endpoint issues when the real problem is likely model availability