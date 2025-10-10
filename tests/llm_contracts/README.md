# LLM Contract Tests for PRT Chat

This directory contains contract tests for validating that the LLM (Ollama with gpt-oss:20b) can reliably parse natural language queries into structured JSON commands.

## Why Contract Tests?

Contract tests validate the **interface contract** between our application and the LLM. Unlike unit tests or integration tests, contract tests ensure that:

1. The LLM produces **valid JSON** (always)
2. The LLM correctly **identifies intents** (search, select, export, etc.)
3. The LLM accurately **extracts parameters** (tags, locations, dates, IDs)
4. The LLM **never hallucinates** data (doesn't invent contacts, tags, or fields)
5. The LLM handles **edge cases and adversarial inputs** gracefully

These tests run against the **real LLM**, not mocks.

## Test Suites

### 1. Initial Suite (5 tests) - `promptfooconfig.yaml`
Quick smoke test for CI

```bash
npx promptfoo eval -c promptfooconfig.yaml
```

### 2. Comprehensive Suite (45 tests) - `promptfooconfig_comprehensive.yaml`
Full validation for Phase 3 baseline

```bash
npx promptfoo eval -c promptfooconfig_comprehensive.yaml
```

## Running Tests

```bash
cd tests/llm_contracts

# Start Ollama first
ollama serve

# Run comprehensive suite
npx promptfoo eval -c promptfooconfig_comprehensive.yaml

# View results in web UI
npx promptfoo view
```

## Success Criteria

| Metric | Target | Critical? |
|--------|--------|-----------|
| **JSON Validity** | 100% | ✅ YES |
| **Intent Accuracy** | >95% | ✅ YES |
| **Parameter Accuracy** | >90% | ✅ YES |
| **Hallucination Rate** | 0% | ✅ YES |

See full documentation in this file for details on interpreting results, troubleshooting, and establishing baselines.
