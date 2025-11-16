# Feature: LLM Provider Parity Architecture

**Type**: Feature Enhancement
**Priority**: High
**Complexity**: Medium
**Estimated Time**: 6-8 hours

## Problem Statement

The current LLM architecture has significant duplication and feature gaps between providers:

### Current State Issues:
- **Code Duplication**: Tool definitions, system prompts, and chat logic duplicated between OllamaLLM (1,516 lines) and LlamaCppLLM (597 lines)
- **Feature Gap**: LlamaCppLLM has only 9 read-only tools vs OllamaLLM's 45+ tools with full write operations
- **Architecture Inconsistency**: OllamaLLM inherits from BaseLLM, LlamaCppLLM doesn't
- **Maintenance Burden**: Changes to tools/prompts must be made in multiple places
- **User Experience Gap**: LlamaCppLLM users lack advanced features (SQL, directories, relationships)

### Evidence from Analysis:
```
OllamaLLM:     1,516 lines, 45+ tools, full CRUD + backups
LlamaCppLLM:     597 lines,  9 tools, read-only operations
Duplication:    ~400 lines of identical tool/prompt logic
```

## Solution Overview

Implement an enhanced base class architecture that eliminates duplication while bringing LlamaCppLLM to feature parity through code reuse and protocol abstraction.

### Core Insight:
90% of LLM functionality is identical - only the communication protocol differs:
- **Same**: Tool definitions, system prompts, conversation management, backup logic
- **Different**: HTTP/JSON vs direct llama.cpp calls, response parsing formats

## Detailed Architecture

### Phase 1: Shared Infrastructure Components

#### 1.1 Centralized Tool Registry
**File**: `prt_src/llm_tools.py` (NEW)

```python
class LLMToolRegistry:
    """Centralized registry eliminating tool definition duplication."""

    @classmethod
    def get_all_tools(cls, api: PRTAPI, disabled_tools: set = None) -> List[Tool]:
        """Return all 45+ tools with consistent definitions."""
        return [
            *cls._create_read_tools(api),      # 10 search/info tools
            *cls._create_write_tools(api),     # 15 CRUD tools with backups
            *cls._create_advanced_tools(api),  # 10 SQL/directory/memory tools
            *cls._create_relationship_tools(api) # 10 relationship tools
        ]
```

**Benefits**:
- Single source of truth for all tool definitions
- Automatic parity - new tools available to both providers
- Centralized tool filtering/configuration

#### 1.2 Enhanced Base Class
**File**: `prt_src/llm_base.py` (ENHANCED)

```python
class BaseLLM:
    """Enhanced base class with shared functionality and protocol abstraction."""

    def __init__(self, api: PRTAPI, config_manager: LLMConfigManager):
        self.tools = LLMToolRegistry.get_all_tools(api, config_manager.tools.disabled_tools)
        self.prompt_generator = LLMPromptGenerator(self.tools)
        self.tool_executor = LLMToolExecutor(api)  # Shared backup system

    def chat(self, message: str) -> str:
        """Unified chat logic delegating protocol specifics to subclasses."""
        # Shared conversation management
        # Protocol-specific communication (abstract method)
        # Shared tool execution with backup system
        # Unified response handling
```

**Benefits**:
- Eliminates 90% of duplicated chat logic
- Shared backup system for both providers
- Protocol abstraction enables future providers

#### 1.3 Unified Prompt System
**File**: `prt_src/llm_prompts.py` (NEW)

```python
class LLMPromptGenerator:
    """Provider-aware system prompt generation."""

    def create_system_prompt(self, provider: str = "ollama") -> str:
        return "\n\n".join([
            self._get_core_identity(),           # Shared
            self._get_security_rules(),          # Shared
            self._get_tool_descriptions(),       # Shared (from registry)
            self._get_provider_guidance(provider), # Provider-specific
            self._get_common_patterns()          # Shared
        ])
```

**Benefits**:
- Eliminates prompt duplication
- Provider-specific customization where needed
- Consistent user experience across providers

### Phase 2: Provider Implementation Simplification

#### 2.1 Streamlined OllamaLLM
**File**: `prt_src/llm_ollama.py` (REFACTORED)

```python
class OllamaLLM(BaseLLM):
    """Ollama HTTP API protocol implementation."""

    def __init__(self, api: PRTAPI, config_manager: LLMConfigManager = None, **kwargs):
        super().__init__(api, config_manager)  # Gets all 45+ tools automatically
        # Only Ollama-specific initialization (base_url, model, keep_alive)

    def _send_message_with_tools(self, messages: List[Dict], tools: List[Tool]) -> Dict:
        """Ollama native API tool calling (existing functionality)."""

    def _extract_tool_calls(self, response: Dict) -> List[Dict]:
        """Parse Ollama's native tool call format."""
```

**Changes**:
- ~1000 lines removed (moved to shared base)
- Retains existing Ollama-specific optimizations
- Zero behavior changes for existing users

#### 2.2 Enhanced LlamaCppLLM
**File**: `prt_src/llm_llamacpp.py` (ENHANCED)

```python
class LlamaCppLLM(BaseLLM):
    """Direct GGUF model protocol implementation with FULL feature set."""

    def __init__(self, api: PRTAPI, model_path: str, config_manager: LLMConfigManager = None, **kwargs):
        super().__init__(api, config_manager)  # Gets all 45+ tools automatically
        # Only LlamaCpp-specific initialization (model loading)

    def _send_message_with_tools(self, messages: List[Dict], tools: List[Tool]) -> str:
        """Direct llama.cpp model inference with tool guidance in prompt."""

    def _extract_tool_calls(self, response: str) -> List[Dict]:
        """Parse JSON tool calls from text response."""
```

**Changes**:
- Inherits all 45+ tools automatically
- Gets write operations + backup system
- Gets advanced features (SQL, directories, relationships)
- Maintains performance advantages of direct model access

### Phase 3: Configuration and Documentation Parity

#### 3.1 Model Configuration Enhancement
**File**: `prt_src/llm_supported_models.py` (ENHANCED)

Add LlamaCpp model definitions:
```python
LLAMACPP_MODELS = [
    SupportedModelInfo(
        model_name="llama-3.2-8b-instruct.Q4_K_M.gguf",
        friendly_name="llama3-8b-q4",
        provider="llamacpp",
        # ... hardware requirements
    ),
    # More GGUF model configurations
]
```

#### 3.2 Usage Documentation
**File**: `docs/LLM_Integration/llamacpp_usage.md` (NEW)

Document LlamaCpp usage patterns:
```bash
# Direct GGUF model usage
python -m prt_src.cli --llm-provider llamacpp --llm-model models/llama-3.2-8b.gguf chat

# All features now available
python -m prt_src.tui --llm-provider llamacpp  # Full tool set
```

## Implementation Plan

### Phase 1: Infrastructure (3-4 hours)
1. **Create `llm_tools.py`**: Extract all tool definitions from OllamaLLM
2. **Enhance `llm_base.py`**: Add shared chat logic and tool execution
3. **Create `llm_prompts.py`**: Extract and unify system prompt generation
4. **Add `LLMToolExecutor`**: Centralized tool execution with backup system

**Acceptance Criteria**:
- [ ] All tools available through centralized registry
- [ ] Enhanced BaseLLM with protocol abstraction
- [ ] Unified prompt generation system
- [ ] Shared backup/tool execution system

### Phase 2: Provider Refactoring (2-3 hours)
1. **Refactor OllamaLLM**: Remove duplicated code, inherit from enhanced BaseLLM
2. **Enhance LlamaCppLLM**: Inherit from BaseLLM, implement protocol methods
3. **Verify compatibility**: Ensure existing Ollama functionality unchanged

**Acceptance Criteria**:
- [ ] OllamaLLM behavior unchanged for existing users
- [ ] LlamaCppLLM has access to all 45+ tools
- [ ] Both providers support write operations with backups
- [ ] Code duplication reduced by 90%

### Phase 3: Configuration & Testing (1-2 hours)
1. **Add GGUF model configurations**: Update supported models registry
2. **Create usage documentation**: Examples for both providers
3. **Integration testing**: Verify all tools work with both providers
4. **Performance testing**: Validate LlamaCpp performance advantages

**Acceptance Criteria**:
- [ ] LlamaCpp models listed in `list-models` command
- [ ] Documentation parity between providers
- [ ] All integration tests passing for both providers
- [ ] Performance benchmarks demonstrate LlamaCpp advantages

## Expected Outcomes

### Feature Parity Achieved:
- ✅ **45+ tools** available to both providers
- ✅ **Write operations** work with LlamaCppLLM (tags, notes, relationships)
- ✅ **Advanced features** available (SQL execution, directory generation, memory management)
- ✅ **Security features** included (backup system, SQL validation)

### Code Quality Improvements:
- ✅ **90% reduction** in duplicated code
- ✅ **Single source of truth** for tool definitions and prompts
- ✅ **Protocol abstraction** enables easy addition of future providers
- ✅ **Unified testing** strategy for all providers

### User Experience Enhancements:
- ✅ **Consistent functionality** regardless of provider choice
- ✅ **Performance options** (Ollama for convenience, LlamaCpp for speed)
- ✅ **Clear model selection** with both network and local options
- ✅ **Seamless switching** between providers via configuration

## Migration Strategy

### Backward Compatibility:
- **Ollama users**: Zero breaking changes, identical behavior maintained
- **LlamaCpp users**: Only feature additions, no removed functionality
- **Configuration**: Existing configs continue working unchanged
- **API contracts**: All existing API methods preserved

### Rollout Plan:
1. **Phase 1**: Infrastructure changes (no user-facing changes)
2. **Phase 2**: Provider refactoring (behind feature flags if needed)
3. **Phase 3**: Documentation and configuration updates
4. **Phase 4**: Announcement of LlamaCpp feature parity

## Success Metrics

### Code Quality:
- **Lines of code**: Reduce total LLM code by 30%+
- **Duplication ratio**: < 5% duplicated functionality
- **Test coverage**: Maintain 90%+ coverage for both providers
- **Complexity**: Simplified architecture with clear separation of concerns

### Feature Completeness:
- **Tool parity**: 100% tool availability across providers
- **Feature parity**: Write operations, backups, advanced features available to both
- **Configuration parity**: Model selection, tool configuration unified
- **Documentation parity**: Equal quality docs for both providers

### Performance:
- **LlamaCpp speed**: Validate performance improvements over Ollama
- **Memory usage**: Monitor resource consumption for both providers
- **Initialization time**: Compare startup times between providers
- **Throughput**: Benchmark tokens/second for each provider

## Risk Mitigation

### Technical Risks:
- **Integration complexity**: Mitigate with incremental development and extensive testing
- **Performance regression**: Benchmark before/after changes
- **Compatibility issues**: Maintain existing API contracts exactly

### User Experience Risks:
- **Behavior changes**: Implement behind feature flags initially
- **Documentation gaps**: Create comprehensive migration guides
- **Configuration confusion**: Clear examples for both providers

## Future Benefits

This architecture enables:
- **Easy provider addition**: New LLM providers follow same pattern
- **Centralized improvements**: Tool enhancements benefit all providers automatically
- **A/B testing**: Easy comparison between providers for performance optimization
- **Specialized optimizations**: Provider-specific tuning without code duplication

---

**Dependencies**: None
**Breaking Changes**: None (backward compatible)
**Testing Requirements**: Integration tests for both providers, performance benchmarks
**Documentation Updates**: LlamaCpp usage guide, updated architecture documentation