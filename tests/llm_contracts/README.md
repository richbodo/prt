# LLM Contract Tests

**Status:** Deferred - Using integration tests instead

## Current Approach

We've deferred contract testing tools (like promptfoo) in favor of **Python integration tests** that test the actual app behavior.

**Why?**
- Integration tests work reliably with our tool-calling orchestration
- Easier to debug and maintain
- Test real app code, not just raw LLM behavior
- No dependency on external contract testing frameworks

## Integration Tests

See: `tests/integration/test_llm_one_query.py`

Example:
```python
def test_count_contacts_integration():
    api = PRTAPI()
    llm = OllamaLLM(api=api)
    response = llm.chat("How many contacts do I have?")
    # Verify response contains correct count
```

## System Prompt Reference

The `system_prompt.txt` file in this directory is kept for reference but **is not actively used**. The actual system prompt is dynamically generated in `prt_src/llm_ollama.py` at the `_create_system_prompt()` method.

## Future: Contract Tests

When we're ready to add contract tests (testing LLM behavior with specific prompts/tools), we'll evaluate:
- Promptfoo (if Ollama tool calling support improves)
- Custom Python-based contract testing
- Other LLM testing frameworks

For now: Integration tests provide sufficient coverage.
