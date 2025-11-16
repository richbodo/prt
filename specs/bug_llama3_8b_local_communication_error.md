# Bug: Ollama Communication Error with llama3-8b-local Model

## Bug Description

The llama3-8b-local model fails to communicate properly with Ollama, returning a `400 Client Error: Bad Request for url: http://localhost:11434/api/chat` when attempting to send chat requests. This error occurs specifically with `llama3-8b-local:latest` while other Ollama models (such as `mistral:7b-instruct`) work correctly with the same communication code.

**Symptoms:**
- Model preloads successfully into Ollama memory
- Health check appears to work (returns coroutine, indicating connection is established)
- Chat requests fail with HTTP 400 Bad Request error
- Other Ollama models (mistral, gpt-oss) work perfectly with identical code paths

**Expected Behavior:**
- llama3-8b-local should communicate successfully like other Ollama models
- Chat requests should return valid responses instead of HTTP 400 errors
- Model should be upgraded from "Unsupported" status to official support

**Actual Behavior:**
- HTTP 400 Bad Request errors during chat communication
- Model remains in "Unsupported" status with ❓ indicator
- Users cannot use llama3-8b-local for chat functionality

## Problem Statement

The llama3-8b-local model lacks the proper configuration and optimizations needed to communicate effectively with Ollama's API. While the model registry recognizes it and it can be preloaded, the chat communication fails due to missing model-specific handling similar to what was implemented for mistral-7b-instruct.

## Solution Statement

Implement llama3-8b-local support by adding model-specific optimizations similar to the successful mistral-7b-instruct implementation. This includes temperature optimization, enhanced system prompt guidance, and upgrade to official support status. The solution follows the exact pattern established for mistral support while accounting for Llama3's different characteristics.

## Steps to Reproduce

1. Ensure llama3-8b-local is available in Ollama: `ollama list | grep llama3-8b-local`
2. Verify model shows as "Unsupported" in PRT: `python -m prt_src.cli list-models`
3. Attempt to use model for chat: `python -m prt_src.cli --model llama3-8b-local --chat "hello"`
4. Observe TUI shows "✅ LLM: ONLINE │ READY" but actual chat fails with 400 error
5. Run test script: `python test_llama3_communication.py` to see the exact error

## Root Cause Analysis

**Analysis of the Issue:**

1. **Missing Model-Specific Optimizations**: The llama3-8b-local model is not recognized by the model-specific optimization functions in `prt_src/llm_ollama.py`. Unlike mistral models which have dedicated `_is_mistral_model()` detection and temperature optimization, llama3-8b-local uses default settings that may not work well for tool calling.

2. **Experimental Support Status**: The model is marked as "experimental" in `prt_src/llm_supported_models.py` with the note "Limited tool calling support. May not work with all PRT features." This indicates it was expected to have issues.

3. **Missing System Prompt Guidance**: The `prt_src/llm_prompts.py` file has aggressive tool calling guidance for mistral models but no specific guidance for llama3-8b models, which may need different prompting strategies.

4. **Registry Naming Mismatch**: The model appears as `llama3-8b-local:latest` in Ollama but the supported models registry only defines `llama3:8b`. This could cause resolution issues.

**Evidence from Analysis:**
- Mistral models have `_is_mistral_model()` detection and temperature override to 0.3 maximum
- Mistral has special tool call ID generation with 9 alphanumeric characters
- Mistral has aggressive system prompts: "🚨 CRITICAL FOR MISTRAL: ALWAYS USE TOOL CALLING 🚨"
- llama3-8b-local lacks all of these optimizations
- The recent URL fix (removesuffix) helps all models but doesn't solve model-specific issues

## Relevant Files

Use these files to fix the bug:

- **`prt_src/llm_ollama.py`** - Add llama3-8b-local model detection and temperature optimization similar to mistral implementation
- **`prt_src/llm_supported_models.py`** - Update llama3:8b status from "experimental" to "official" and add llama3-8b-local variant
- **`prt_src/llm_prompts.py`** - Add llama3-8b-specific system prompt guidance optimized for its limited tool calling capabilities
- **`test_llama3_communication.py`** - Test script that reproduces the 400 error (already exists for validation)

### New Files

- **`tests/integration/test_llama3_8b_local_communication.py`** - Integration test to validate the fix and prevent regressions

## Step by Step Tasks

### Step 1: Add Model Detection and Optimization

Add llama3-8b model detection and temperature optimization to `prt_src/llm_ollama.py`:
- Add `_is_llama3_8b_model()` method similar to `_is_mistral_model()`
- Implement temperature optimization (possibly lower than mistral's 0.3, try 0.2)
- Add model-specific initialization logging
- Apply optimization in `__init__` method similar to mistral pattern

### Step 2: Update Model Registry Support Status

Update model support in `prt_src/llm_supported_models.py`:
- Change `llama3:8b` support status from "experimental" to "official"
- Add entry for `llama3-8b-local` variant with proper specifications
- Update hardware requirements and context size based on testing
- Add appropriate use cases and notes about tool calling optimization

### Step 3: Add Model-Specific System Prompt Guidance

Enhance system prompt generation in `prt_src/llm_prompts.py`:
- Add llama3-8b model detection in `_get_core_identity()` method
- Implement simplified tool calling guidance (less aggressive than mistral)
- Focus on fallback patterns since tool calling support is more limited
- Add guidance for handling tool calling failures gracefully

### Step 4: Create Integration Tests

Create comprehensive integration test in `tests/integration/test_llama3_8b_local_communication.py`:
- Test model creation and initialization
- Test health check and preload functionality
- Test basic chat communication (no 400 errors)
- Test tool calling behavior and fallbacks
- Test temperature optimization is applied correctly
- Mock Ollama responses to ensure deterministic testing

### Step 5: Update Documentation and Registry

Update model documentation and registry:
- Add llama3-8b-local to officially supported models list
- Document the optimization settings and use cases
- Update CLI help text to reflect official support
- Add troubleshooting notes if needed

### Step 6: Validation Testing

Run comprehensive validation tests:
- Verify `python test_llama3_communication.py` no longer shows 400 errors
- Test model shows as "✅ Official" in `list-models` output
- Test both direct chat and TUI chat interfaces work
- Verify no regressions in existing models (mistral, gpt-oss)
- Run full test suite to ensure no broader regressions

## Validation Commands

Execute every command to validate the bug is fixed with zero regressions.

- `python test_llama3_communication.py` - Verify no more 400 errors, both models should work
- `python -m prt_src.cli list-models` - Verify llama3-8b-local shows as officially supported
- `python -m prt_src.cli --model llama3-8b-local --chat "hello"` - Test direct CLI chat works
- `python -m prt_src --model llama3-8b-local` - Test TUI chat interface works
- `python -m prt_src.cli --model mistral-7b-instruct --chat "hello"` - Verify mistral still works
- `./prt_env/bin/pytest tests/integration/test_llama3_8b_local_communication.py -v` - Run new integration tests
- `./prt_env/bin/pytest tests/integration/test_llm_integration_mocked.py -v` - Verify no regression in existing LLM tests
- `./prt_env/bin/pytest tests/ -k "not integration" -x` - Run unit tests to ensure no regressions
- `./prt_env/bin/ruff check prt_src/ --fix` - Ensure code quality standards
- `./prt_env/bin/black prt_src/` - Ensure consistent code formatting

## Notes

**Implementation Strategy:**
- Follow the exact pattern established for mistral-7b-instruct support
- Start with conservative temperature settings (0.2) and adjust based on testing
- Use simplified prompts since Llama3-8b has more limited tool calling than mistral
- Add comprehensive logging to help debug any remaining issues

**Key Success Metrics:**
- No more HTTP 400 errors when using llama3-8b-local
- Model upgraded from "❓ Unsupported" to "✅ Official" status
- Chat functionality works in both CLI and TUI interfaces
- All existing model support continues to work without regression

**Risk Mitigation:**
- Implementation is additive only (no changes to existing model support)
- Comprehensive test coverage prevents regressions
- Conservative optimization settings reduce risk of new issues
- Pattern follows proven successful approach from mistral implementation