# LLM Integration - Simplified Approach

**Start Date:** October 10, 2025
**Last Updated:** October 13, 2025
**Philosophy:** Start with absolute minimum, grow based on evidence

## Current Status: Phase 1 - Proving ONE Tool Works

### Where We Are Now

✅ **Code Simplified** - Reduced from 15 tools to 1 tool (`search_contacts`)
- File: `prt_src/llm_ollama.py` lines 150-348
- Other 14 tools commented out with PHASE 2 marker
- System prompt dynamically includes only active tools

❌ **Tool Calling Not Working** - Critical blocker discovered
- Promptfoo contract tests: 0/15 passing (0%)
- LLM responds with generic text, never calls tools
- Response: "I'm here to help you manage your personal contact database..."
- No `tool_calls` property in any LLM response

✅ **Unit Tests Passing** - 53/56 tests pass (94.6%)
- ChatContextManager, DisplayContext, ResultsFormatter, SelectionService
- Time: 0.17 seconds
- These test supporting infrastructure, not LLM integration

⚠️ **No Integration Tests** - Need to create these
- `tests/integration/` directory exists but is empty
- This is where we'll test the actual app flow

### What We Discovered

**Problem 1: Scope Creep**
- Documentation said "1 tool", code had 15 tools
- PR #129 merged with additional complexity from parallel LLM work
- Now fixed - back to 1 tool

**Problem 2: Tool Calling Broken**
- Promptfoo tests Ollama directly (not through our app)
- llama3.2:3b may not support tool calling reliably
- OR promptfoo's Ollama provider doesn't support tools correctly
- OR tool schema format is wrong

**Problem 3: Wrong Testing Approach**
- Contract tests (promptfoo) test raw LLM behavior
- But our app orchestrates tools through Python code
- Need integration tests that call `OllamaLLM.chat()` directly

### Current Architecture

```python
# prt_src/llm_ollama.py

class OllamaLLM:
    def _create_tools(self):
        return [
            Tool(
                name="search_contacts",
                description="Search for contacts by name, email, or other criteria",
                parameters={...},
                function=self.api.search_contacts
            ),
            # 14 other tools commented out
        ]

    def _create_system_prompt(self):
        # Dynamically includes only active tools
        return f"""You are an AI assistant for PRT...

        AVAILABLE TOOLS:
        {tools_description}  # Only search_contacts now

        INSTRUCTIONS:
        1. Use tools to get real data
        2. Don't make up information
        ..."""
```

**The system prompt is GOOD** - it's simple, dynamic, and includes only active tools.

## Next Steps: Get ONE Test Working

### Approach 1: Python Integration Test (RECOMMENDED)
Create `tests/integration/test_llm_one_query.py`:
```python
def test_count_contacts():
    """Integration: 'How many contacts?' should return correct count."""
    api = PRTAPI()
    llm = OllamaLLM(api=api)

    # Get actual count
    all_contacts = api.list_all_contacts()
    expected_count = len(all_contacts)

    # Ask LLM
    response = llm.chat("How many contacts do I have?")

    # Verify response contains correct number
    assert str(expected_count) in response
```

**Why this works:**
- Tests through our actual app code
- Uses our tool execution infrastructure
- Doesn't depend on promptfoo's Ollama support

### Approach 2: Debug Promptfoo Tool Calling
- Research if promptfoo supports Ollama tool calling
- Check if llama3.2:3b supports tools natively
- May need different model (mistral, qwen2.5, etc.)

### Approach 3: Manual Testing First
Before automating, just verify it works:
```bash
python -m prt_src.tui
# Navigate to chat screen
# Type: "How many contacts do I have?"
# See if LLM calls search_contacts tool
```

## What We Have (Working Parts)

✅ **OllamaLLM class** (`prt_src/llm_ollama.py`):
- Tool registration system
- Tool execution with error handling
- Conversation history management
- Dynamic system prompt generation

✅ **PRTAPI** that returns comprehensive data:
```python
api.search_contacts("Alice")
# Returns: [{"id": 1, "name": "Alice", "email": "...", "tags": [...], ...}]
```

✅ **Unit tests** for supporting services (53/56 passing)

## What Doesn't Work Yet

❌ **Tool calling** - LLM never calls tools (tested via promptfoo)
❌ **Contract tests** - 0/15 passing (tool calling issue)
❌ **Integration tests** - Don't exist yet (need to create)
❌ **Manual validation** - Haven't tested through TUI chat screen

## Key Principles (Unchanged)

1. **Start with 1 tool, not 15** - ✅ DONE
2. **Tools ARE intents** - No separate intent system
3. **Test before building** - Manual testing, then automated
4. **Measure before modifying** - Let evidence drive decisions
5. **The "10x rule"** - Each sophistication level costs 10x more effort

## Files Changed (Phase 1)

- `prt_src/llm_ollama.py` - Commented out 14 tools, kept search_contacts
- `tests/llm_contracts/promptfooconfig_minimal.yaml` - Created 1-test config
- `docs/LLM_Integration/README.md` - Updated with current reality (this file)

## External References

Three documents guided this approach:
- `EXTERNAL_DOCS/Model_Tips/How_to_architect_llm_systems.txt`
- `EXTERNAL_DOCS/Model_Tips/building_reliable_llm_db_systems.md`
- `EXTERNAL_DOCS/Model_Tips/tech_docs_for_oss20b.md`

All three emphasize: **Start simple, grow deliberately, measure constantly.**

## Immediate Action Items

**Priority 1: Verify Tool Calling Works**
- [ ] Manual test via TUI chat screen
- [ ] Watch logs: `tail -f prt_data/prt.log`
- [ ] Verify tool execution happens

**Priority 2: Create One Integration Test**
- [ ] Write `tests/integration/test_llm_one_query.py`
- [ ] Test: "How many contacts do I have?"
- [ ] Verify correct count returned

**Priority 3: Debug or Bypass Promptfoo**
- [ ] Research if promptfoo supports Ollama tools
- [ ] Try different model if needed
- [ ] OR skip contract tests, use integration tests only

## Test Results

### Unit Tests: ✅ 53/56 PASSED (94.6%)
```
tests/unit/test_chat_context_manager.py: PASSED
tests/unit/test_display_context.py: PASSED
tests/unit/test_results_formatter.py: PASSED (3 skipped)
tests/unit/test_selection_service.py: PASSED
Time: 0.17s
```

### Contract Tests: ❌ 0/15 PASSED (0%)
```
ALL TESTS FAILED - LLM never calls tools
Response: "I'm here to help you manage your personal contact database..."
No tool_calls property in response
Issue: Either promptfoo doesn't support Ollama tools OR llama3.2:3b can't do tools
```

### Integration Tests: ⚠️ NO TESTS
```
tests/integration/ directory is empty
Need to create these
```

---

**Bottom Line:** We've simplified the code (1 tool), but discovered tool calling doesn't work in our test setup. Next step: Verify it actually works through the app, then decide on testing strategy.
