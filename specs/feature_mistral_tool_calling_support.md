# Feature: Mistral-7B-Instruct-v0.3 Tool Calling Support

## Feature Description
Implement comprehensive tool calling support for the `mistral:7b-instruct` model (Mistral-7B-Instruct-v0.3) available in PRT. Based on Ollama model inspection, the current `mistral:7b-instruct` model has "tools" capability and corresponds to Mistral-7B-Instruct-v0.3, which officially supports function calling. However, the model currently returns JSON artifacts instead of executing tools, indicating a configuration or integration issue rather than a fundamental model limitation.

This feature will fix the tool calling integration for our specific Mistral-7B-Instruct-v0.3 model, ensuring it properly executes tools instead of returning code snippets. The focus is on maximizing the capabilities of our existing model rather than adding new models.

## User Story
As a PRT user with limited hardware resources
I want to use the efficient Mistral-7B-Instruct-v0.3 model with full tool calling capability
So that I can interact with my contact database using natural language commands without needing the larger gpt-oss:20b model

## Problem Statement
The current `mistral:7b-instruct` model (Mistral-7B-Instruct-v0.3) in PRT returns JSON code snippets and instructions instead of executing available tools when users request database operations. When a user asks "Show me the first few contacts in the db", the model responds with JavaScript-like code examples rather than calling the `search_contacts` or `list_all_contacts` tools.

Analysis reveals that:
- The model has "tools" capability per `ollama show mistral:7b-instruct`
- It corresponds to Mistral-7B-Instruct-v0.3, which officially supports function calling
- The issue is likely in PRT's tool calling configuration or prompt formatting for Mistral models

## Solution Statement
Fix the tool calling integration for our existing Mistral-7B-Instruct-v0.3 model by implementing Mistral-specific configurations and optimizations. Based on the official Mistral documentation and the model's confirmed tool calling capabilities, this includes:

1. **Tool Calling Configuration**: Implement proper tool calling format compatible with Mistral-7B-Instruct-v0.3
2. **Model Registry Update**: Update model registry to indicate tool calling support for `mistral:7b-instruct`
3. **Prompt Optimization**: Implement Mistral-specific tool calling prompt formats and parameters
4. **Temperature Tuning**: Use optimal temperature settings (0.1-0.3) for tool calling reliability
5. **Tool Call ID Support**: Ensure proper tool call ID handling as required by Mistral models

## Relevant Files
Use these files to implement the feature:

### Core Model Registry and Configuration
- **`prt_src/llm_supported_models.py`** - Model registry that needs new Mistral models with tool calling capabilities clearly indicated
- **`prt_src/llm_factory.py`** - Model resolution and creation logic that may need Mistral-specific configurations
- **`prt_src/llm_ollama.py`** - Ollama provider implementation where tool calling behavior can be optimized for Mistral models
- **`prt_src/config.py`** - Configuration management for any Mistral-specific settings needed

### Testing and Validation
- **`tests/test_llm_supported_models.py`** - Tests for new model registry entries and validation
- **`tests/integration/test_llm_integration_mocked.py`** - Integration tests for tool calling behavior
- **`tests/integration/test_ollama_integration.py`** - Ollama-specific integration tests

### Documentation and User Guidance
- **`docs/TUI/LLM_Configuration.md`** - User guidance for selecting appropriate models
- **`EXTERNAL_DOCS/promptfoo/site/docs/providers/mistral.md`** - Reference documentation about Mistral tool calling

### New Files
- **`tests/integration/test_mistral_tool_calling.py`** - Comprehensive integration tests specifically for Mistral tool calling functionality
- **`docs/LLM_Integration/mistral_configuration.md`** - Detailed configuration guide for Mistral models

## Implementation Plan
### Phase 1: Analysis and Configuration
Analyze the current Ollama integration for Mistral models, review the official Mistral-7B-Instruct-v0.3 tool calling documentation, and implement proper tool calling format and parameters based on Mistral's specifications.

### Phase 2: Tool Calling Integration
Fix the tool calling implementation for `mistral:7b-instruct` by adding Mistral-specific configurations, implement proper tool call ID handling (9 alphanumeric characters as per Mistral spec), and ensure optimal temperature settings for reliable tool execution.

### Phase 3: Testing and Validation
Create comprehensive tests to validate tool calling behavior with Mistral-7B-Instruct-v0.3, test the specific user scenario that currently fails, and ensure reliable tool execution across all database operations.

## Step by Step Tasks

### Step 1: Analyze Current Mistral Integration
- Review current `mistral:7b-instruct` configuration in `llm_ollama.py`
- Examine tool calling format being used and compare with Mistral specifications
- Identify specific configuration gaps causing JSON artifacts instead of tool execution
- Document the exact issue preventing proper tool calling

### Step 2: Update Model Registry
- Update `mistral:7b-instruct` entry in `SUPPORTED_MODELS` to indicate tool calling support
- Add specific notes about Mistral-7B-Instruct-v0.3 capabilities
- Include hardware requirements and optimization recommendations
- Update model use cases to include "Tool calling" for database operations

### Step 3: Implement Mistral Tool Calling Format
- Add Mistral-specific tool calling configuration in `llm_ollama.py`
- Implement proper tool call ID generation (9 alphanumeric characters)
- Set optimal temperature settings (0.1-0.3) for tool calling reliability
- Ensure chat template and prompt formatting match Mistral-7B-Instruct-v0.3 expectations

### Step 4: Create Tool Calling Integration Tests
- Write comprehensive tests in `test_mistral_tool_calling.py`
- Test basic tool calling: `search_contacts`, `list_all_contacts`, `get_contact_details`
- Test complex tool chains: search → get details → create note
- Test error handling and fallback behavior
- Validate tool call ID format and handling

### Step 5: Fix Model Registry Tests
- Update unit tests in `test_llm_supported_models.py` for corrected model entry
- Test model validation and support checking functions
- Verify friendly name resolution works correctly
- Test that `mistral:7b-instruct` is properly recognized as tool-calling capable

### Step 6: Validate Real-World Usage
- Test the exact user scenario: "Show me the first few contacts in the db"
- Verify tools are executed instead of returning JSON artifacts
- Test with debug database to ensure consistent behavior
- Validate performance and response quality meets user expectations

### Step 7: Update Documentation
- Update `docs/TUI/LLM_Configuration.md` with corrected Mistral capabilities
- Create `docs/LLM_Integration/mistral_configuration.md` with setup details
- Document optimal settings for Mistral-7B-Instruct-v0.3 tool calling
- Update user guidance to properly reflect model capabilities

### Step 8: Run Validation Commands
- Execute all validation commands to ensure zero regressions
- Test both new functionality and existing model compatibility
- Verify Mistral tool calling works reliably across different query types
- Confirm no impact on other model functionality

## Testing Strategy
### Unit Tests
- Model registry validation for new Mistral entries
- Hardware requirement calculations and recommendations
- Model name resolution and aliasing functionality
- Configuration loading and validation for Mistral-specific settings

### Integration Tests
- Tool calling functionality with new Mistral models
- End-to-end database operations through tool calls
- Error handling and graceful fallbacks
- Performance and response quality compared to existing models
- Cross-model compatibility and behavior consistency

### Edge Cases
- Model not available in Ollama installation
- Network connectivity issues during model loading
- Tool calling failures and recovery scenarios
- Mixed tool calling support in multi-model configurations
- Hardware resource constraints with larger models

## Acceptance Criteria
- `mistral:7b-instruct` (Mistral-7B-Instruct-v0.3) properly executes tools instead of returning JSON artifacts
- Tool calling works reliably with `mistral:7b-instruct` for all database operations
- User query "Show me the first few contacts in the db" executes `list_all_contacts` or `search_contacts` tool
- Model registry correctly indicates that `mistral:7b-instruct` supports tool calling
- Tool call IDs are properly generated as 9 alphanumeric characters per Mistral specification
- Temperature settings are optimized (0.1-0.3) for reliable tool calling performance
- Documentation accurately reflects Mistral-7B-Instruct-v0.3 capabilities and configuration
- All existing tests continue to pass with no regressions

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `source ./init.sh` - Initialize development environment
- `ollama show mistral:7b-instruct` - Verify Mistral model capabilities (should show "tools" capability)
- `./prt_env/bin/python -c "from prt_src.llm_supported_models import SUPPORTED_MODELS; print(SUPPORTED_MODELS.get('mistral:7b-instruct', 'Not found'))"` - Verify model registry entry
- `./prt_env/bin/python -c "from prt_src.llm_factory import create_llm; llm = create_llm(model='mistral:7b-instruct'); print('✅ Mistral 7B Instruct v0.3 loaded')"` - Test model loading
- `./prt_env/bin/python -c "from prt_src.llm_factory import create_llm; llm = create_llm(model='mistral:7b-instruct'); result = llm.chat('Show me the first few contacts in the db'); print('Tool calling result:', result)"` - Test tool calling functionality
- `./prt_env/bin/pytest tests/test_llm_supported_models.py -v` - Run model registry tests
- `./prt_env/bin/pytest tests/integration/test_mistral_tool_calling.py -v` - Run Mistral-specific integration tests
- `./prt_env/bin/pytest tests/integration/test_llm_integration_mocked.py -k mistral -v` - Run existing LLM integration tests for Mistral
- `./prt_env/bin/pytest tests/ -k "not integration" -v` - Run all unit tests to verify no regressions
- `python -m prt_src --debug --model mistral:7b-instruct` - Test TUI integration with fixed model
- `./prt_env/bin/ruff check prt_src/ tests/ --fix` - Ensure code quality standards
- `./prt_env/bin/black prt_src/ tests/` - Ensure consistent code formatting

## Notes
- The Mistral-7B-Instruct-v0.3 model is already available via Ollama as `mistral:7b-instruct`
- Tool calling is supported in the model but requires proper configuration in PRT's integration
- Tool calling performance should be optimized using Mistral's recommended settings (temperature 0.1-0.3)
- Tool call IDs must be exactly 9 alphanumeric characters per Mistral specification
- The model supports extended vocabulary (32768 tokens) and v3 Tokenizer features
- Consider implementing fallback behavior if tool calling fails with Mistral models
- Hardware requirements are reasonable (4.4GB model size with Q4_K_M quantization)
- Future consideration: Explore extended context length (32768) for complex tool calling scenarios