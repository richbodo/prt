# Feature: Enhanced Multiple LLM Model Support

## Feature Description
Enhance PRT's existing LLM model support to provide better discovery, validation, and user experience for multiple models. While the codebase already has a robust multi-model architecture through the OllamaModelRegistry and LLMFactory, this feature will improve the user experience by:

1. Adding command-line options to list available models with better formatting and information
2. Adding model validation to ensure only supported models are used
3. Enhancing model selection with clear documentation of supported models
4. Improving error messages and user guidance for model configuration
5. Adding a whitelist mechanism for officially supported models vs. experimental ones

The application currently supports any model available through Ollama, but should provide clear guidance on which models are officially tested and supported.

## User Story
As a PRT user with different hardware capabilities
I want to easily discover and select appropriate LLM models for my system
So that I can choose the best model for my computational resources and get optimal performance

## Problem Statement
While PRT already has sophisticated multi-model support through its registry and factory pattern, users lack clear guidance on:
- Which models are officially supported vs. experimental
- How to discover what models are available on their system
- What hardware requirements different models have
- Clear error messages when models aren't available
- Command-line validation that prevents launching with unsupported models

The existing `list-models` command exists but needs enhancement for better user experience.

## Solution Statement
Enhance the existing model management system by:
1. Adding a whitelist of officially supported models (gpt-oss:20b, mistral:7b-instruct)
2. Improving the `list-models` command to show support status, hardware requirements, and clear recommendations
3. Adding model validation at startup with helpful error messages
4. Enhancing command-line help and documentation for model selection
5. Improving the overall user experience around model discovery and selection

## Relevant Files

### Core LLM Infrastructure (Already Implemented)
- **prt_src/llm_model_registry.py**: Model discovery and caching via Ollama API
  - Contains `OllamaModelRegistry` with LRU cache and friendly name generation
  - Handles model discovery, alias resolution, and extended model information
  - Already supports cache management and health checking

- **prt_src/llm_factory.py**: Model alias resolution and LLM instantiation
  - Contains `resolve_model_alias()` and `create_llm()` factory functions
  - Handles provider auto-detection and model validation
  - Already supports both Ollama and LlamaCpp providers

- **prt_src/config.py**: LLM configuration management
  - Contains `LLMConfig` dataclass with all model settings
  - Default model is currently `gpt-oss:20b`
  - Supports fallback models and provider selection

### CLI Interface (Needs Enhancement)
- **prt_src/cli.py**: CLI with existing `--model` option and `list-models` command
  - Lines 2891-2896: Existing `--model` option with help text
  - Lines 2973-3031: Existing `list-models` command that needs enhancement
  - Lines 3093-3094: Error message that needs improvement

- **prt_src/tui/__main__.py**: TUI entry point with `--model` option
  - Lines 55-60: Existing `--model` argument parsing
  - Already passes model to PRTApp constructor

### Configuration and Validation (Needs Enhancement)
- **prt_src/tui/app.py**: TUI app initialization with model parameter
  - Lines 124-127: Constructor accepts model parameter
  - Line 202: LLM service creation that could benefit from validation

### New Files
#### Enhanced Model Support
- **prt_src/llm_supported_models.py**: Whitelist of officially supported models with metadata
- **tests/test_llm_supported_models.py**: Unit tests for supported model validation

## Implementation Plan

### Phase 1: Foundation - Supported Models Registry
Create a centralized registry of officially supported models with metadata about hardware requirements, descriptions, and status.

### Phase 2: Core Implementation - Enhanced Commands and Validation
Improve the existing `list-models` command and add validation for model selection with better error messages.

### Phase 3: Integration - Enhanced User Experience
Integrate the new validation and messaging throughout the CLI and TUI interfaces for a consistent experience.

## Step by Step Tasks

### Step 1: Create Supported Models Registry
Create `prt_src/llm_supported_models.py` to define officially supported models with metadata including hardware requirements, descriptions, and current status.

### Step 2: Write Unit Tests for Registry
Create comprehensive unit tests in `tests/test_llm_supported_models.py` to validate the supported models registry functionality.

### Step 3: Enhance list-models Command
Improve the existing `list-models` command in `prt_src/cli.py` to show supported status, hardware requirements, and better formatting with recommendations.

### Step 4: Add Model Validation Functions
Extend `prt_src/llm_factory.py` with validation functions that check if a model is officially supported and provide helpful warnings for unsupported models.

### Step 5: Improve Error Messages and Help Text
Update error messages throughout `prt_src/cli.py` and `prt_src/tui/__main__.py` to provide better guidance on model selection and troubleshooting.

### Step 6: Add Integration Tests
Create integration tests to verify the enhanced model selection workflow works correctly with both supported and unsupported models.

### Step 7: Update Documentation
Update help text and docstrings to reflect the enhanced model support capabilities and provide clear guidance to users.

### Step 8: Run Validation Commands
Execute all validation commands to ensure the feature works correctly with zero regressions.

## Testing Strategy

### Unit Tests
- Test supported models registry functionality
- Test model validation logic with various scenarios
- Test enhanced list-models command output formatting
- Test error message generation for different failure modes

### Integration Tests
- Test model selection workflow with supported models
- Test model selection workflow with unsupported models
- Test CLI and TUI integration with the enhanced model validation
- Test fallback behavior when preferred models aren't available

### Edge Cases
- Model not available in Ollama registry
- Ollama service not running
- Invalid model names or aliases
- Models that exist in Ollama but aren't officially supported
- Network connectivity issues during model discovery
- Empty model registry responses

## Acceptance Criteria

1. **Enhanced Model Discovery**: `list-models` command shows supported status, hardware requirements, and clear recommendations
2. **Model Validation**: Startup validates selected model and provides helpful warnings/errors for unsupported models
3. **Better Error Messages**: Clear, actionable error messages when models aren't available or supported
4. **Backward Compatibility**: Existing model selection continues to work without changes
5. **Documentation**: Help text and examples clearly explain model selection options
6. **Performance**: Model validation doesn't significantly impact startup time
7. **Officially Supported Models**: gpt-oss:20b and mistral:7b-instruct are marked as officially supported
8. **User Guidance**: Clear recommendations for model selection based on hardware capabilities

## Validation Commands

Execute every command to validate the feature works correctly with zero regressions.

- `./prt_env/bin/pytest tests/test_llm_supported_models.py -v` - Test new supported models registry
- `./prt_env/bin/pytest tests/test_llm_factory.py -v` - Test enhanced factory validation
- `./prt_env/bin/pytest tests/test_cli.py -v` - Test enhanced CLI commands
- `./prt_env/bin/pytest tests/ -k "llm" -v` - Run all LLM-related tests
- `python -m prt_src.cli list-models` - Test enhanced list-models command
- `python -m prt_src.cli --model gpt-oss-20b chat` - Test supported model selection
- `python -m prt_src.cli --model mistral-7b-instruct chat` - Test supported model selection
- `python -m prt_src.cli --model unsupported-model chat` - Test unsupported model handling
- `python -m prt_src.tui --model gpt-oss-20b` - Test TUI with supported model
- `python -m prt_src.tui --model invalid-model` - Test TUI with invalid model
- `./scripts/run-ci-tests.sh` - Run all CI tests to ensure no regressions
- `./prt_env/bin/ruff check prt_src/ tests/` - Lint new and modified code
- `./prt_env/bin/black prt_src/ tests/` - Format new and modified code

## Notes

**Key Architectural Decisions:**
1. **Leverage Existing Infrastructure**: Build upon the robust OllamaModelRegistry and LLMFactory rather than replacing them
2. **Whitelist Approach**: Use a whitelist of officially supported models while still allowing experimental use of other models
3. **Graceful Degradation**: Provide warnings rather than hard failures for unsupported models to maintain flexibility
4. **Hardware Awareness**: Include hardware requirement information to help users make appropriate model choices

**Implementation Notes:**
- The codebase already has sophisticated LLM infrastructure - this feature enhances the user experience rather than replacing core functionality
- Model aliases like `gpt-oss-20b` (from `gpt-oss:20b`) are already supported through the friendly_name property
- The existing cache system (5-minute TTL, LRU with 100 model limit) should be preserved
- Validation should be fast to avoid impacting startup performance

**Future Considerations:**
- Could add automatic hardware detection and model recommendations
- Could integrate with model benchmarking data to show performance characteristics
- Could add model download assistance for missing supported models
- Could expand to support additional LLM providers beyond Ollama and LlamaCpp