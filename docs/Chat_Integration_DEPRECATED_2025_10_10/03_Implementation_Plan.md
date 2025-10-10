# Chat Screen Implementation Plan

This document outlines the phase-by-phase plan for implementing the Chat screen as a natural language database interface with comprehensive testing and configurable safeguards.

## 🎯 Current Status

**Last Updated**: 2025-10-10

| Phase | Status | Tests | Notes |
|-------|--------|-------|-------|
| Phase 0: Test Infrastructure | ✅ COMPLETE | 53 integration, 56 unit | All CI tests passing |
| Phase 1: Deterministic Components | ✅ COMPLETE | 53 unit tests | 100% coverage |
| Phase 2: LLM Bridge with Mocks | ⏸️ DEFERRED | - | Will do after Phase 3 |
| Phase 3: LLM Contract Testing | 🔜 NEXT | - | Validate LLM first (risk mitigation) |
| Phase 4: Workflow Implementation | ⏳ PENDING | - | After Phase 2 |
| Phase 5: Real LLM Integration | ⏳ PENDING | - | After Phase 4 |
| Phase 6: Advanced Features | ⏳ PENDING | - | After Phase 5 |
| Phase 7: Regression & Docs | ⏳ PENDING | - | Ongoing |

**Current Focus**: Phase 3 (LLM Contract Testing) - Validate that real LLM produces correct outputs before building integration layer.

---

## Overview

**Goal**: Build a conversational database interface where users can search, select, and act on data using natural language, with the same underlying workflows as the search screen.

**Key Principles**:
1. **Test-Driven**: Build deterministic components with TDD, validate LLM behavior with contract tests
2. **Layered Testing**: Fast unit tests → mocked integration tests → LLM contract tests → E2E tests
3. **Configurable**: All LLM settings and safeguards exposed via JSON config
4. **Developer-First**: Full control for experimentation, future "safe mode" for end users
5. **Reusable**: Share components between Chat and Search screens

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                   Chat Screen (TUI)                     │
│  - User input handling                                  │
│  - Display formatting                                   │
│  - Mode management (EDIT/NAV)                           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              LLM Database Bridge                        │
│  - Natural language → structured JSON commands          │
│  - Context management (conversation history)            │
│  - Prompt building                                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           Search-Select-Act Workflow                    │
│  - Execute search queries                               │
│  - Manage selection state                               │
│  - Dispatch actions (export, delete, edit)              │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│             Shared Components                           │
│  - ResultsFormatter (list, table, cards, tree)         │
│  - SelectionService (app-level state)                   │
│  - ExportService (JSON, directory, CSV)                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  PRTAPI (Database)                      │
│  - Search, create, update, delete operations            │
│  - Data validation                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 0: Test Infrastructure & Configuration Setup 🛠️ ✅ COMPLETE

**Goal**: Establish testing foundation and configuration system before feature work

**Priority**: HIGH (blocks all other phases)

**Status**: ✅ COMPLETE (PR #127 merged)

### Tasks

#### 0.1 Configuration System
- [x] Create `LLMConfigManager` class ✅
- [x] Add LLM config sections to `prt_config.json` schema ✅
- [x] Implement config loading with validation ✅
- [x] Add config file migration (existing → new format) ✅
- [x] Update `OllamaLLM` to use config (backward compatible) ✅
- [x] Document configuration in `LLM_Configuration.md` ✅

#### 0.2 Unit Test Infrastructure
- [x] Create `tests/unit/` directory structure ✅
- [x] Add fixture library for contacts, relationships, notes ✅
  - `fixture_contact(name, email, location, tags)` ✅
  - `fixture_contacts_batch(count)` ✅
- [x] Configure pytest markers: ✅
  - `@pytest.mark.unit` - Fast unit tests (< 1s) ✅
  - `@pytest.mark.integration` - Integration with mocks (< 5s) ✅
  - `@pytest.mark.contract` - LLM contract tests (1-5m)
  - `@pytest.mark.slow` - E2E tests (5-10m)
  - `@pytest.mark.requires_llm` - Requires real LLM
- [x] Set up pytest configuration (`pytest.ini`) ✅

#### 0.3 Mock LLM Infrastructure
- [x] Implement `MockLLMService` class ✅
  - Pattern-based response matching ✅
  - Response library for common intents ✅
- [x] Created integration test fixtures ✅
  - mock_app, pilot_screen fixtures ✅
  - test_db fixture for database tests ✅

#### 0.4 Promptfoo Setup
- [x] Install promptfoo: `npm install -g promptfoo` ✅
- [x] Create `tests/llm_contracts/` directory ✅
- [x] Write `promptfooconfig.yaml` configuration ✅
- [x] Create initial test suite (5 critical cases): ✅
  - Intent classification (search, select, export) ✅
  - Parameter extraction (tags, locations) ✅
  - JSON schema validation ✅
- [x] Document how to run: `npx promptfoo eval` ✅
- [x] Add to CI (weekly scheduled run) ✅

#### 0.5 CI Configuration
- [x] Update GitHub Actions workflow: ✅
  ```yaml
  test-unit:
    - pytest -m unit --maxfail=1

  test-integration:
    - pytest -m integration --maxfail=3

  test-llm-contracts:
    if: github.event.schedule  # Weekly
    - npx promptfoo eval
  ```
- [x] Add coverage reporting: `pytest --cov=prt_src/tui` ✅
- [ ] Set coverage thresholds (unit: >90%, integration: >80%) (deferred)

### Exit Criteria
- ✅ Configuration system loads LLM settings from JSON
- ✅ Can run `pytest -m unit` (< 1s, even with no tests yet)
- ✅ Can run `pytest -m integration` with mock LLM
- ✅ Can run `npx promptfoo eval` with sample tests
- ✅ CI runs unit tests on every commit
- ✅ Documentation complete

### Files Created
- `prt_src/config.py` - Configuration management
- `tests/unit/conftest.py` - Unit test fixtures
- `tests/integration/conftest.py` - Mock LLM fixtures
- `tests/llm_contracts/promptfoo.yaml` - Contract tests
- `docs/TUI/LLM_Configuration.md` ✅

### Estimated Effort
- Configuration: 4-6 hours
- Test infrastructure: 3-4 hours
- Mock LLM: 2-3 hours
- Promptfoo: 2-3 hours
- CI setup: 1-2 hours
- **Total: 12-18 hours**

---

## Phase 1: Deterministic Components (TDD) 🧱 ✅ COMPLETE

**Goal**: Build and test the parts that don't need LLM

**Priority**: HIGH (foundation for everything else)

**Status**: ✅ COMPLETE (PR #127 merged)

### Tasks

#### 1.1 ResultsFormatter (TDD)
**Write tests first, then implement**

- [x] Test: Numbered list formatting ✅
  - Basic list with indices [1], [2], [3] ✅
  - With selection markers [ ] and [✓] ✅
  - With pagination (showing 1-10 of 50) ✅
  - Empty results ✅
- [x] Test: Table formatting (Rich tables) ✅
  - Contacts table (name, email, location, tags) ✅
  - Column width handling (deferred - future enhancement)
- [x] Test: Card formatting ✅
  - Detailed contact cards ✅
  - Card separator formatting (deferred - future enhancement)
- [ ] Test: Tree formatting (deferred - Phase 6 advanced feature)
  - Hierarchical relationships
  - Contact with nested relationships/notes
- [x] Test: Compact formatting ✅
  - Comma-separated names ✅
  - One-line summaries ✅
- [x] Implement `ResultsFormatter` class ✅
  - `render()` method with mode parameter ✅
  - Private methods for each format ✅
  - Helper methods for truncation, wrapping ✅

#### 1.2 DisplayContext (TDD)
- [x] Test: Basic context creation ✅
  - Create DisplayContext with results ✅
  - Track result metadata ✅
  - Validate display modes ✅
- [x] Test: Context operations ✅
  - has_results() method ✅
  - result_count() method ✅
  - clear_results() method ✅
  - update_results() method ✅
  - copy() for immutability ✅
- [x] Implement `DisplayContext` dataclass ✅
- [ ] Advanced context generation (deferred - will implement with LLM bridge in Phase 2)

#### 1.3 ChatContextManager (TDD)
- [x] Test: Conversation history ✅
  - Add user/assistant/system messages ✅
  - Prune old history (keep last N) ✅
  - Preserve system prompt when pruning ✅
  - Handle empty history ✅
- [x] Test: Message management ✅
  - get_messages_for_llm() ✅
  - get_last_user_message() ✅
  - clear_history() ✅
  - message_count() ✅
- [x] Implement `ChatContextManager` class ✅
- [ ] Prompt building with DisplayContext (deferred - Phase 2)

#### 1.4 SelectionService (TDD)
- [x] Test: Selection operations ✅
  - Add items to selection (select(), select_range()) ✅
  - Remove items from selection (deselect()) ✅
  - Clear selection ✅
  - Toggle individual items ✅
- [x] Test: Selection state queries ✅
  - is_selected() ✅
  - get_selected_ids() ✅
  - Returns copies (not internal state) ✅
- [x] Test: Bulk operations ✅
  - select_all_from_list() ✅
  - select_from_results() ✅
- [x] Implement `SelectionService` class ✅

### Exit Criteria
- ✅ 100% unit test coverage for these components
- ✅ All tests run in < 1 second (0.04s for ResultsFormatter tests)
- ✅ Can format results in all modes (numbered list, table, card, compact)
- ✅ Can manage conversation context (history, pruning, message formatting)
- ✅ Can track selections (select, deselect, toggle, clear, bulk ops)

### Files Created
- ✅ `prt_src/tui/formatters/results.py` - ResultsFormatter
- ✅ `prt_src/tui/formatters/display_context.py` - DisplayContext dataclass
- ✅ `prt_src/tui/services/chat_context_manager.py` - ChatContextManager
- ✅ `prt_src/tui/services/selection_service.py` - SelectionService
- ✅ `tests/unit/test_results_formatter.py` - 13 tests (10 passing, 3 skipped future enhancements)
- ✅ `tests/unit/test_display_context.py` - 10 tests (all passing)
- ✅ `tests/unit/test_chat_context_manager.py` - 14 tests (all passing)
- ✅ `tests/unit/test_selection_service.py` - 16 tests (all passing)

### Actual Effort
- ResultsFormatter: ~6 hours (tests + implementation)
- DisplayContext: ~3 hours
- ChatContextManager: ~4 hours
- SelectionService: ~4 hours
- **Total: ~17 hours** (within original estimate of 16-21 hours)

---

## Phase 2: LLM Bridge with Mocks 🌉 ⏸️ DEFERRED

**Goal**: Build parsing layer, test with mock LLM

**Priority**: HIGH (core functionality)

**Status**: ⏸️ DEFERRED - Will implement after Phase 3 (per risk mitigation strategy)

### Tasks

#### 2.1 System Prompt Design
- [ ] Design JSON command schema
  - Intent types: search, refine, select, export, view_details
  - Parameter structures for each intent
  - Error responses
- [ ] Write system prompt
  - Explain database schema
  - Define command format
  - Provide examples
  - Specify constraints (no hallucination)
- [ ] Make prompt configurable
  - Load from `config.llm_prompts`
  - Support file-based overrides
  - Validate on load

#### 2.2 Integration Tests with Mock LLM
**Write tests first**

- [ ] Test: Search intent parsing
  - Simple searches ("show me tech contacts")
  - Filtered searches (tags, location, date ranges)
  - Multi-filter searches ("tech contacts in SF from 2024")
- [ ] Test: Refinement intent parsing
  - Add constraints ("just the ones in Oakland")
  - Remove constraints ("ignore location")
  - Multiple refinements in sequence
- [ ] Test: Selection intent parsing
  - ID lists ("select 1, 2, 5")
  - Ranges ("select 1-10", "first 5", "last 3")
  - Special cases ("all", "none", "clear")
  - Content-based ("select everyone in SF")
- [ ] Test: Export intent parsing
  - Format detection ("export to json", "export for directory")
  - Destination ("save to /path/")
- [ ] Test: Error handling
  - Invalid JSON from LLM
  - Missing required fields
  - Unknown intent types
  - Malformed parameters
- [ ] Test: Multi-turn conversations
  - Context continuity
  - Refinement chains
  - Selection accumulation

#### 2.3 Implement LLMDatabaseBridge
- [ ] Implement `parse_user_intent()` method
  - Build prompt with context
  - Call LLM
  - Parse JSON response
  - Validate command structure
- [ ] Implement command validation
  - JSON schema validation
  - Intent whitelist
  - Parameter type checking
  - Required field verification
- [ ] Implement error handling
  - Graceful JSON parse failures
  - Retry logic (optional)
  - Fallback responses
  - User-friendly error messages
- [ ] Add debug logging
  - Log prompts (if configured)
  - Log responses (if configured)
  - Log parse errors (always)
  - Log timing (if configured)

#### 2.4 Permission Checking
- [ ] Implement permission guards
  - Check `allow_create` before create operations
  - Check `allow_update` before updates
  - Check `allow_delete` before deletes
  - Check `read_only_mode` for all writes
- [ ] Implement confirmation dialogs (UI components)
  - Generic confirmation dialog widget
  - Specialized dialogs (delete, bulk ops)
  - Show affected items
  - Configurable based on `require_confirmation` settings

### Exit Criteria
- ✅ All integration tests pass with mock LLM
- ✅ Can parse 5 critical intent types
- ✅ Graceful error handling for invalid responses
- ✅ Tests run in < 5 seconds
- ✅ Permission system integrated

### Files Created
- `prt_src/llm_bridge.py` - LLMDatabaseBridge class
- `prt_src/llm_prompts.py` - System prompt templates
- `prt_src/tui/widgets/confirmation_dialog.py` - Confirmation dialog
- `tests/integration/test_llm_bridge.py` - 30-40 tests
- `tests/integration/test_permissions.py` - 10-15 tests

### Estimated Effort
- System prompt: 2-3 hours
- Integration tests: 6-8 hours
- LLMDatabaseBridge: 5-6 hours
- Permission system: 3-4 hours
- **Total: 16-21 hours**

---

## Phase 3: LLM Contract Testing (High Risk) ⚠️ 🔜 NEXT

**Goal**: Validate that real LLM produces correct outputs

**Priority**: HIGH (de-risks core functionality)

**Status**: 🔜 NEXT PHASE - Per risk mitigation strategy, validate LLM behavior BEFORE building integration layer

**Why This Order?**: Phase 3 validates that the LLM can reliably produce the JSON outputs we need. If it can't, we'll know before investing time in building Phase 2's integration layer. This de-risks the project significantly.

### Tasks

#### 3.1 Comprehensive Promptfoo Test Suite
- [ ] Critical: Intent classification (10 tests)
  - Search intent variants
  - Selection intent variants
  - Export intent variants
  - Refinement intent variants
  - View details intent
- [ ] Critical: Parameter extraction (10 tests)
  - Tag extraction ("tech", "python", "AI")
  - Location extraction ("SF", "San Francisco", "bay area")
  - Date extraction ("this year", "2024", "last month")
  - ID extraction ([1,2,3], "1 and 2", "first 5")
- [ ] Critical: JSON validation (5 tests)
  - Well-formed JSON (always)
  - Required fields present
  - Correct data types
  - No extra fields
- [ ] Edge cases (10 tests)
  - Empty queries
  - Ambiguous queries
  - Very long queries
  - Special characters
  - Multi-language (if supported)
- [ ] Adversarial inputs (10 tests)
  - Injection attempts
  - Hallucination tests (shouldn't make up data)
  - Contradictory instructions
  - Malformed natural language

#### 3.2 Baseline Establishment
- [ ] Run full suite with local LLM
- [ ] Document results:
  - Intent accuracy (target: >95%)
  - Parameter accuracy (target: >90%)
  - JSON validity (target: 100%)
  - Hallucination rate (target: 0%)
- [ ] Save baseline results to `tests/llm_contracts/baseline.json`
- [ ] Create comparison script: `compare_prompt_results.py`

#### 3.3 System Prompt Iteration
- [ ] Identify failure patterns
- [ ] Iterate on system prompt:
  - Add clarifying examples
  - Strengthen constraints
  - Improve schema descriptions
- [ ] Re-run promptfoo after each change
- [ ] Track accuracy improvements
- [ ] Converge on stable prompt (3-5 iterations expected)

#### 3.4 Alternative Model Testing
- [ ] Test with faster model (llama3.2:3b) for CI
  - Compare accuracy vs main model
  - Measure speed improvement
  - Decide if acceptable for CI
- [ ] Document model compatibility
  - Which models work well
  - Which models fail
  - Recommended models per use case

### Exit Criteria
- ✅ 95%+ accuracy on critical intents
- ✅ 100% valid JSON output
- ✅ 0% hallucinated data (doesn't make up contacts/IDs)
- ✅ Baseline established for regression detection
- ✅ Regression test suite runs in CI (weekly)

### Files Created
- `tests/llm_contracts/promptfoo.yaml` - 45-50 test cases
- `tests/llm_contracts/baseline.json` - Baseline results
- `tests/llm_contracts/compare_results.py` - Comparison script
- `tests/llm_contracts/README.md` - How to run and interpret

### Estimated Effort
- Test suite creation: 6-8 hours
- Baseline establishment: 2-3 hours (slow LLM)
- Prompt iteration: 4-6 hours (3-5 cycles)
- Alternative model testing: 2-3 hours
- **Total: 14-20 hours**

---

## Phase 4: Workflow Implementation 🔄

**Goal**: Connect all pieces, implement actions

**Priority**: MEDIUM (builds on previous phases)

### Tasks

#### 4.1 SearchSelectActWorkflow
- [ ] Implement workflow class
  - Execute search queries
  - Manage selection state
  - Dispatch actions
  - Track operation history
- [ ] Add action handlers:
  - Export (JSON, directory, CSV)
  - Delete (with confirmation)
  - Edit (open in form)
  - View details (show full record)
  - Add tags (bulk operation)
  - Remove tags (bulk operation)
- [ ] Add undo support (optional):
  - Track reversible operations
  - Implement undo stack
  - Add undo command

#### 4.2 ChatScreen Integration
- [ ] Wire up LLMDatabaseBridge
- [ ] Connect ChatContextManager
- [ ] Implement message handling:
  - Parse user message
  - Route to appropriate handler (search/select/export)
  - Format and display response
  - Update context
- [ ] Add response formatting:
  - Use ResultsFormatter
  - Add helpful hints ("say 'select #' to choose")
  - Show progress indicators
  - Show error messages
- [ ] Add keyboard shortcuts:
  - Ctrl+L: Clear conversation
  - Ctrl+U: Undo last message
  - Ctrl+E: Export last results

#### 4.3 Export Service
- [ ] Implement JSON export
  - Full contact data
  - Include relationships
  - Include notes
  - Pretty-printed
- [ ] Implement directory export
  - Format for `make_directory.py`
  - Include profile images
  - Create metadata file
- [ ] Implement CSV export
  - Flattened contact data
  - Configurable columns
  - Handle special characters

#### 4.4 Integration Tests
- [ ] Test: Complete workflows (with mock LLM)
  - Search → Select → Export
  - Search → Refine → Refine → Select → Export
  - Select all → Bulk tag
  - Error recovery (failed export, permission denied)
- [ ] Test: Multi-turn conversations
  - Context continuity
  - State preservation
  - Error recovery
- [ ] Test: Edge cases
  - Empty results
  - Large result sets (1000+ items)
  - Rapid queries (stress test)

### Exit Criteria
- ✅ Can execute complete workflows with mock LLM
- ✅ All actions work (export, delete, edit, etc.)
- ✅ Integration tests pass
- ✅ Error handling for all failure modes

### Files Created
- `prt_src/tui/workflows/search_select_act.py` - Workflow class
- `prt_src/tui/services/export.py` - Export service
- `prt_src/tui/screens/chat.py` - Updated with LLM integration
- `tests/integration/test_chat_workflow.py` - 20-30 tests

### Estimated Effort
- Workflow implementation: 5-6 hours
- ChatScreen integration: 6-8 hours
- Export service: 4-5 hours
- Integration tests: 4-5 hours
- **Total: 19-24 hours**

---

## Phase 5: Real LLM Integration & Manual Testing 🎯

**Goal**: Test with real LLM, fix issues

**Priority**: MEDIUM (validation phase)

### Tasks

#### 5.1 Manual Testing Scenarios
- [ ] Basic searches
  - "show me all my contacts"
  - "find tech people"
  - "contacts in San Francisco"
  - "people I met in 2024"
- [ ] Refinement chains
  - Search → "just the ones in Oakland" → "only colleagues"
- [ ] Selection variations
  - "select 1, 2, 3"
  - "select the first 5"
  - "select all"
  - "select everyone in SF from that list"
- [ ] Export workflows
  - "export to json"
  - "export for directory maker"
  - "save as csv"
- [ ] Error scenarios
  - Empty results
  - Permission denied (delete with allow_delete=false)
  - Invalid selections (out of range)

#### 5.2 Issue Tracking & Fixes
- [ ] Document all failures
  - What user said
  - What LLM returned
  - What should have happened
  - Prompt improvement needed?
- [ ] Fix prompt issues
  - Adjust system prompt
  - Re-run promptfoo to verify
  - Update baseline
- [ ] Fix code issues
  - Parsing bugs
  - Context bugs
  - UI bugs

#### 5.3 Conversation Refinement
- [ ] Test multi-turn conversations (5-10 turns)
- [ ] Verify context continuity
- [ ] Test refinement accumulation
- [ ] Test conversation reset

#### 5.4 Performance Optimization
- [ ] Measure token usage per query type
  - Minimal context: ~500-1000 tokens
  - Detailed context: ~2000-4000 tokens
  - Adaptive context: ~1000-2000 tokens
- [ ] Measure response times
  - Simple queries: ~10-20s
  - Complex queries: ~20-30s
  - Context-heavy queries: ~30-40s
- [ ] Optimize hot paths
  - Reduce token usage where possible
  - Cache system prompt (don't rebuild)
  - Prune context aggressively

### Exit Criteria
- ✅ Critical workflows work with real LLM
- ✅ Response times acceptable (< 30s for 90% of queries)
- ✅ Context continuity works
- ✅ Promptfoo tests still passing after fixes
- ✅ No critical bugs in manual testing

### Files Created
- `docs/TUI/Chat_Manual_Test_Plan.md` - Test scenarios
- `docs/TUI/Chat_Known_Issues.md` - Issue tracker
- Performance benchmark results

### Estimated Effort
- Manual testing: 8-10 hours (spread over multiple sessions)
- Issue fixes: 6-10 hours (depends on findings)
- Performance optimization: 3-4 hours
- **Total: 17-24 hours**

---

## Phase 6: Advanced Features & Polish 🚀

**Goal**: Add polish, ensure stability

**Priority**: LOW (nice-to-haves)

### Tasks

#### 6.1 Content-Based Selection
- [ ] Implement filter-based selection
  - "select everyone in SF"
  - "select people I haven't talked to in 6 months"
  - "select colleagues who work at Google"
- [ ] Update system prompt with examples
- [ ] Add promptfoo tests
- [ ] Test with real LLM

#### 6.2 Pagination
- [ ] Implement "show more" command
- [ ] Implement "show next 10"
- [ ] Implement "show previous"
- [ ] Update context to track pagination state

#### 6.3 Bulk Operations with Confirmation
- [ ] Add confirmation for risky actions:
  - Delete confirmation (show items)
  - Bulk operation warnings (>10 items)
- [ ] Implement confirmation dialog UI
- [ ] Make thresholds configurable

#### 6.4 Conversation Management
- [ ] Add conversation save/load
  - Save conversation to file
  - Load previous conversation
  - List saved conversations
- [ ] Add conversation export
  - Export as markdown
  - Export as JSON
  - Include timestamps

#### 6.5 Help System
- [ ] Add inline help
  - "help" command shows capabilities
  - "examples" shows common queries
- [ ] Add tooltips/hints
  - Show hints based on context
  - "Try: 'select 1-5' or 'select all'"

### Exit Criteria
- ✅ All advanced features working
- ✅ Tests passing
- ✅ Documentation updated

### Files Created
- Various enhancements to existing files
- Help documentation

### Estimated Effort
- Content-based selection: 4-5 hours
- Pagination: 3-4 hours
- Confirmations: 2-3 hours
- Conversation management: 3-4 hours
- Help system: 2-3 hours
- **Total: 14-19 hours**

---

## Phase 7: Regression Suite & Documentation 📚

**Goal**: Ensure long-term stability

**Priority**: LOW (ongoing maintenance)

### Tasks

#### 7.1 Comprehensive Regression Suite
- [ ] Expand promptfoo to 60-80 tests
  - Cover all supported intents
  - Cover all parameter types
  - Cover all edge cases
  - Cover adversarial inputs
- [ ] Set up automated regression testing
  - Run weekly in CI
  - Compare against baseline
  - Alert on regressions
  - Generate report

#### 7.2 Performance Benchmarking
- [ ] Create benchmark suite
  - Measure token usage (min/avg/max)
  - Measure response times (p50/p95/p99)
  - Measure accuracy (intent/parameter)
- [ ] Document baseline performance
- [ ] Set up performance monitoring
  - Track over time
  - Alert on degradation

#### 7.3 User Documentation
- [ ] Write user guide:
  - How to use chat interface
  - Common queries
  - Tips and tricks
  - Troubleshooting
- [ ] Write developer guide:
  - How to modify system prompt
  - How to add new intents
  - How to debug LLM issues
  - How to run tests

#### 7.4 Future Enhancements Planning
- [ ] Document future features:
  - Function calling (when Ollama supports it)
  - Multi-model fallback
  - Streaming responses
  - Conversation branching
  - Voice input (future)

### Exit Criteria
- ✅ Comprehensive regression suite
- ✅ Performance benchmarks documented
- ✅ User and developer documentation complete
- ✅ Future roadmap defined

### Files Created
- `tests/llm_contracts/regression_suite.yaml` - Full test suite
- `docs/TUI/Chat_User_Guide.md` - User documentation
- `docs/TUI/Chat_Developer_Guide.md` - Developer documentation
- `docs/TUI/Chat_Performance_Benchmarks.md` - Performance data

### Estimated Effort
- Regression suite: 6-8 hours
- Performance benchmarking: 3-4 hours
- Documentation: 8-10 hours
- **Total: 17-22 hours**

---

## Summary: Total Effort Estimate

| Phase | Effort | Priority | Blocks |
|-------|--------|----------|--------|
| Phase 0: Infrastructure | 12-18h | HIGH | Everything |
| Phase 1: Deterministic Components | 16-21h | HIGH | Phase 2-7 |
| Phase 2: LLM Bridge | 16-21h | HIGH | Phase 3-7 |
| Phase 3: LLM Contract Testing | 14-20h | HIGH | Phase 5 |
| Phase 4: Workflow Implementation | 19-24h | MEDIUM | Phase 5-6 |
| Phase 5: Real LLM Integration | 17-24h | MEDIUM | Phase 6-7 |
| Phase 6: Advanced Features | 14-19h | LOW | - |
| Phase 7: Regression & Docs | 17-22h | LOW | - |
| **Total** | **125-169 hours** | | |

**Realistic Timeline** (assuming 10-20 hours/week):
- **Minimum**: 6-8 weeks (20h/week, focused)
- **Expected**: 8-12 weeks (15h/week, realistic)
- **Comfortable**: 12-17 weeks (10h/week, sustainable)

---

## Risk Mitigation

**Highest Risks → Address First:**

1. ⚠️⚠️⚠️ **LLM intent parsing** → Phase 3 (contract tests before heavy dev)
2. ⚠️⚠️ **Configuration system** → Phase 0 (foundation for everything)
3. ⚠️⚠️ **Test infrastructure** → Phase 0 (enables fast iteration)
4. ⚠️ **Context management** → Phase 1 (complex logic, test thoroughly)
5. ⚠️ **Permission system** → Phase 2 (safety-critical)

**Build in this order:**
1. Infrastructure & config (Phase 0)
2. Deterministic components (Phase 1)
3. LLM contract tests (Phase 3) - **validate before building on it**
4. LLM bridge with mocks (Phase 2)
5. Workflows (Phase 4)
6. Real LLM integration (Phase 5)
7. Polish (Phase 6-7)

**Don't build:**
- Phase 5 before Phase 3 passes (validate LLM works first!)
- Phase 4 before Phase 1 complete (need formatters/context)
- Phase 6-7 before Phase 5 stable (don't polish a broken foundation)

---

## Success Metrics

**Phase 0-3**: Foundation
- ✅ All unit tests pass in < 1s
- ✅ All integration tests pass in < 5s
- ✅ LLM contract tests show 95%+ accuracy
- ✅ Configuration system loads and validates

**Phase 4-5**: Core Functionality
- ✅ Critical workflows work end-to-end
- ✅ Response times < 30s for 90% of queries
- ✅ No critical bugs in manual testing
- ✅ Permission system prevents unintended modifications

**Phase 6-7**: Production Ready
- ✅ All features implemented and tested
- ✅ Comprehensive regression suite (60+ tests)
- ✅ Performance benchmarks documented
- ✅ User and developer documentation complete

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Start with Phase 0** (infrastructure)
3. **Track progress** in GitHub issues
4. **Update plan** as we learn (this is agile, not waterfall!)
5. **Celebrate milestones** (completed phases are achievements!)

Remember: **This is a living document**. Adjust as needed based on what we learn during implementation!
