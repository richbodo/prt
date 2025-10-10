# LLM Contract Tests with Promptfoo

This directory contains contract tests for validating LLM intent parsing accuracy.

## What Are Contract Tests?

Contract tests validate that the LLM consistently produces correct outputs (the "contract") for a defined set of inputs. They catch regressions when prompts change and establish accuracy baselines.

See `docs/Chat_Integration/06_Contract_Testing.md` for complete documentation.

## Quick Start

### Prerequisites

1. **Ollama running** with gpt-oss:20b model:
   ```bash
   ollama serve
   ollama pull gpt-oss:20b
   ```

2. **Promptfoo installed**:
   ```bash
   npm install -g promptfoo
   # or
   npx promptfoo --version
   ```

### Running Tests

```bash
# Run all contract tests
npx promptfoo eval

# Run and open web UI
npx promptfoo eval && promptfoo view

# Save results for baseline comparison
npx promptfoo eval -o results.json
```

### Understanding Results

**Pass rate target**: ≥95% (19/20 tests passing)

**Key metrics**:
- Intent classification accuracy: 100% required
- Parameter extraction accuracy: ≥95%
- JSON validity: 100% required
- Hallucination rate: 0% required

## Phase 0 Test Suite

The initial test suite includes **5 critical tests**:

1. **Search intent classification** - "show me tech contacts"
2. **Selection intent classification** - "select 1, 2, and 5"
3. **Export intent classification** - "export for directory"
4. **Multi-filter parameter extraction** - "python developers in SF"
5. **No hallucinations** - Must not invent contact names

## Files

- `promptfooconfig.yaml` - Promptfoo configuration
- `system_prompt.txt` - System prompt being tested
- `README.md` - This file
- `baseline.json` - Baseline results (created after first passing run)
- `promptfoo_results.json` - Latest test results (generated)

## Baseline Tracking

After tests pass consistently:

```bash
# Establish baseline
npx promptfoo eval -o baseline.json
git add baseline.json
git commit -m "Establish LLM contract test baseline"

# Compare new results to baseline
npx promptfoo eval -o new_results.json
python compare_results.py new_results.json baseline.json
```

## Troubleshooting

### Tests fail intermittently

**Cause**: LLM non-determinism

**Solution**:
- Temperature is already low (0.1)
- Run tests multiple times, accept 90%+ pass rate
- Consider using larger model

### Tests timeout

**Cause**: Model loading delay

**Solution**:
- Preload model: `ollama run gpt-oss:20b "test"`
- Set keep_alive: `ollama run gpt-oss:20b --keep-alive 30m`

### JSON validation failures

**Cause**: LLM returns text instead of pure JSON

**Solution**: Update system_prompt.txt to be more explicit about JSON-only output

## Next Steps (Phase 3)

Phase 3 will expand this suite to 60+ tests covering:
- Edge cases (empty queries, long queries)
- All intent types
- Complex parameter extraction
- Error handling
- Multi-turn conversation context

See `docs/Chat_Integration/03_Implementation_Plan.md` Phase 3 for details.
