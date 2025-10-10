# LLM Contract Testing with Promptfoo

This guide covers contract testing for the Chat screen's LLM integration using [Promptfoo](https://promptfoo.dev), an industry-standard tool for LLM validation and regression detection.

## What is Contract Testing?

**Contract testing** validates that the LLM consistently produces correct outputs for a defined set of inputs, serving as a "contract" between your code and the LLM.

### Why We Need It

**The Problem**:
- LLMs are non-deterministic (same input → different outputs)
- Prompts can break silently when changed
- Can't enumerate all possible user inputs
- Unit tests can't validate actual LLM behavior

**The Solution**:
- Test critical input/output pairs with real LLM
- Detect regressions when prompts change
- Establish accuracy baselines (>95% intent classification)
- Validate zero hallucination rate

See [04_Testing_Strategy.md](./04_Testing_Strategy.md#layer-3-llm-contract-tests-promptfoo-) for how contract tests fit into the overall testing strategy.

---

## Promptfoo Overview

**Promptfoo** is a testing framework specifically designed for LLM applications:

- ✅ **Evaluates prompts against test cases** - Automated testing
- ✅ **Detects regressions** - Compares results against baselines
- ✅ **Supports multiple providers** - Ollama, OpenAI, Claude, etc.
- ✅ **Rich assertions** - JSON validation, regex, custom JavaScript
- ✅ **CI/CD integration** - Run in GitHub Actions, etc.
- ✅ **Baseline tracking** - Save and compare test runs

**Website**: [promptfoo.dev](https://promptfoo.dev)
**Docs**: [promptfoo.dev/docs](https://www.promptfoo.dev/docs/)

---

## Installation

### Prerequisites

- Node.js 18+ (for Promptfoo)
- Ollama running locally (for LLM provider)
- GPT-OSS-20B model pulled (`ollama pull gpt-oss:20b`)

### Install Promptfoo

```bash
# Global installation (recommended)
npm install -g promptfoo

# Verify installation
promptfoo --version

# Or use npx without installing (slower)
npx promptfoo --version
```

### Project Setup

```bash
# Create test directory (if not exists)
mkdir -p tests/llm_contracts

# Initialize promptfoo in project
cd tests/llm_contracts
promptfoo init
```

This creates:
- `promptfooconfig.yaml` - Main configuration
- `prompts/` - Directory for prompt files
- `.promptfoo/` - Cache directory (add to .gitignore)

---

## Configuration

### Basic Configuration

Create `tests/llm_contracts/promptfooconfig.yaml`:

```yaml
description: 'PRT Chat LLM Intent Parsing Contract Tests'

# Prompts to test
prompts:
  - file://system_prompt.txt

# LLM provider configuration
providers:
  - id: ollama:gpt-oss:20b
    config:
      temperature: 0.1  # Low for consistency
      apiBaseUrl: http://localhost:11434/v1

# Default test configuration
defaultTest:
  options:
    provider: ollama:gpt-oss:20b

# Test cases
tests:
  # Intent classification tests
  - description: 'Identifies search intent for tech contacts'
    vars:
      user_message: 'show me all my tech contacts'
    assert:
      - type: is-json
      - type: javascript
        value: JSON.parse(output).intent === 'search'
      - type: javascript
        value: JSON.parse(output).parameters.filters.tags.includes('tech')

  - description: 'Identifies selection intent with ID list'
    vars:
      user_message: 'select 1, 2, and 5'
    assert:
      - type: is-json
      - type: javascript
        value: JSON.parse(output).intent === 'select'
      - type: javascript
        value: JSON.parse(output).parameters.ids.sort().join(',') === '1,2,5'

  - description: 'Identifies export intent'
    vars:
      user_message: 'export them for the directory'
    assert:
      - type: is-json
      - type: javascript
        value: JSON.parse(output).intent === 'export'
      - type: javascript
        value: JSON.parse(output).parameters.format === 'directory'
```

### System Prompt File

Create `tests/llm_contracts/system_prompt.txt` with your actual system prompt:

```
You are a database query assistant for PRT (Personal Relationship Toolkit).

Your job is to translate natural language queries into structured JSON commands.

Available intents:
- search: Search for contacts, relationships, notes, or tags
- select: Select items from current results
- refine: Add or remove filters from current search
- export: Export selected items
- view_details: Show detailed information

Response format (JSON only):
{
  "intent": "search|select|refine|export|view_details",
  "parameters": { ... },
  "explanation": "Brief explanation of what you understood"
}

Examples:
User: "show me tech contacts in SF"
{
  "intent": "search",
  "parameters": {
    "entity_type": "contacts",
    "filters": {
      "tags": ["tech"],
      "location": ["SF", "San Francisco"]
    }
  },
  "explanation": "Searching for contacts tagged 'tech' in San Francisco"
}

IMPORTANT:
- Respond ONLY with valid JSON
- Never make up contact names or data
- Map natural location names (SF → San Francisco)
- Extract all filters from the query
```

### Advanced Configuration

**Multiple prompt variants**:

```yaml
prompts:
  - id: conservative
    file://prompts/conservative_prompt.txt

  - id: detailed
    file://prompts/detailed_prompt.txt

  - id: minimal
    file://prompts/minimal_prompt.txt

# Test all variants
defaultTest:
  options:
    provider: ollama:gpt-oss:20b
```

**Multiple providers (for comparison)**:

```yaml
providers:
  - id: ollama:gpt-oss:20b
    config:
      temperature: 0.1

  - id: ollama:llama3.2:3b
    config:
      temperature: 0.1

  - id: ollama:mistral:7b
    config:
      temperature: 0.1
```

---

## Test Cases

### Critical Test Categories

#### 1. Intent Classification

Validate that the LLM correctly identifies user intent.

```yaml
tests:
  # Search intents
  - description: 'Search: Simple tag query'
    vars:
      user_message: 'show me tech contacts'
    assert:
      - type: is-json
      - type: javascript
        value: JSON.parse(output).intent === 'search'

  - description: 'Search: Multi-filter query'
    vars:
      user_message: 'find python developers in San Francisco hired after 2020'
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          return r.intent === 'search' &&
                 r.parameters.filters.tags.includes('python') &&
                 r.parameters.filters.location.includes('San Francisco');

  # Selection intents
  - description: 'Select: ID list'
    vars:
      user_message: 'select 1, 2, and 3'
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          const ids = r.parameters.ids.sort();
          return r.intent === 'select' && ids.join(',') === '1,2,3';

  - description: 'Select: Range'
    vars:
      user_message: 'select the first 5'
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          return r.intent === 'select' &&
                 (r.parameters.range || r.parameters.ids.length === 5);

  - description: 'Select: All'
    vars:
      user_message: 'select all'
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          return r.intent === 'select' && r.parameters.selection_type === 'all';

  # Export intents
  - description: 'Export: JSON format'
    vars:
      user_message: 'export to json'
    assert:
      - type: javascript
        value: JSON.parse(output).intent === 'export'
      - type: javascript
        value: JSON.parse(output).parameters.format === 'json'

  - description: 'Export: Directory format'
    vars:
      user_message: 'export for directory maker'
    assert:
      - type: javascript
        value: JSON.parse(output).intent === 'export'
      - type: javascript
        value: JSON.parse(output).parameters.format === 'directory'
```

#### 2. Parameter Extraction

Validate that the LLM correctly extracts parameters from queries.

```yaml
tests:
  # Tag extraction
  - description: 'Extract tags: tech, python'
    vars:
      user_message: 'show me tech people who know python'
    assert:
      - type: javascript
        value: |
          const tags = JSON.parse(output).parameters.filters.tags;
          return tags.includes('tech') && tags.includes('python');

  # Location extraction (with normalization)
  - description: 'Normalize location: SF → San Francisco'
    vars:
      user_message: 'contacts in SF'
    assert:
      - type: javascript
        value: |
          const locs = JSON.parse(output).parameters.filters.location;
          return locs.includes('SF') || locs.includes('San Francisco');

  # Date extraction
  - description: 'Extract date range: this year'
    vars:
      user_message: 'people I met this year'
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          const year = new Date().getFullYear();
          return r.parameters.filters.date_range &&
                 r.parameters.filters.date_range.includes(year.toString());
```

#### 3. JSON Schema Validation

Ensure responses are always valid JSON with required fields.

```yaml
tests:
  # All responses must be valid JSON
  - description: 'Valid JSON: Search query'
    vars:
      user_message: 'show me contacts'
    assert:
      - type: is-json

  - description: 'Valid JSON: Selection query'
    vars:
      user_message: 'select 1 and 2'
    assert:
      - type: is-json

  # Required fields must be present
  - description: 'Has required fields: intent'
    vars:
      user_message: 'show me tech contacts'
    assert:
      - type: javascript
        value: 'intent' in JSON.parse(output)

  - description: 'Has required fields: parameters'
    vars:
      user_message: 'show me tech contacts'
    assert:
      - type: javascript
        value: 'parameters' in JSON.parse(output)
```

#### 4. Safety Properties (No Hallucinations)

Validate that the LLM never makes up data.

```yaml
tests:
  # LLM must NOT invent contact names
  - description: 'No hallucinations: Export query'
    vars:
      user_message: 'export the selected contacts'
    assert:
      - type: not-contains
        value: 'Alice'  # Common fake name
      - type: not-contains
        value: 'Bob'
      - type: not-contains
        value: 'John Doe'

  # LLM must NOT invent IDs
  - description: 'No hallucinations: Selection query'
    vars:
      user_message: 'select my favorite contacts'
    assert:
      - type: javascript
        value: |
          const r = JSON.parse(output);
          // Should request clarification, not make up IDs
          return r.intent === 'clarify' || r.parameters.selection_type === 'unclear';
```

#### 5. Edge Cases

Test unusual or ambiguous inputs.

```yaml
tests:
  # Empty/ambiguous queries
  - description: 'Edge case: Empty query'
    vars:
      user_message: ''
    assert:
      - type: is-json
      - type: javascript
        value: JSON.parse(output).intent === 'clarify'

  - description: 'Edge case: Unclear query'
    vars:
      user_message: 'umm, idk, show me something'
    assert:
      - type: is-json

  # Very long queries
  - description: 'Edge case: Long complex query'
    vars:
      user_message: 'show me all tech contacts who know python and are located in San Francisco or Oakland and I met them in the last 6 months and they have notes about meetings'
    assert:
      - type: is-json
      - type: javascript
        value: JSON.parse(output).intent === 'search'
```

---

## Running Tests

### Basic Execution

```bash
# Run all tests
cd tests/llm_contracts
npx promptfoo eval

# Run with specific config
npx promptfoo eval -c promptfooconfig.yaml

# Run and open web UI
npx promptfoo eval && promptfoo view
```

### Output

```
PROMPT 1 (system_prompt.txt)
================================================================================

PROVIDER ollama:gpt-oss:20b
┌─────────┬────────────────────────────────┬────────┬────────────────────┐
│ Test #  │ Description                    │ Pass?  │ Score              │
├─────────┼────────────────────────────────┼────────┼────────────────────┤
│ 1       │ Identifies search intent...    │ ✅ PASS │ 1.00               │
│ 2       │ Identifies selection intent... │ ✅ PASS │ 1.00               │
│ 3       │ Identifies export intent...    │ ✅ PASS │ 1.00               │
│ 4       │ Extract tags: tech, python     │ ✅ PASS │ 1.00               │
│ 5       │ No hallucinations: Export      │ ✅ PASS │ 1.00               │
├─────────┼────────────────────────────────┼────────┼────────────────────┤
│         │ TOTAL                          │ 5/5    │ 100.00%            │
└─────────┴────────────────────────────────┴────────┴────────────────────┘
```

### Detailed Output

```bash
# Show failures only
npx promptfoo eval --verbose

# Show full LLM responses
npx promptfoo eval --output results.json

# Then inspect
cat results.json | jq '.results[] | select(.pass == false)'
```

---

## Baseline Tracking

### Establishing a Baseline

When your tests pass consistently (>95% accuracy), save a baseline:

```bash
# Run tests and save results
npx promptfoo eval -o baseline.json

# Commit baseline to git
git add tests/llm_contracts/baseline.json
git commit -m "Establish LLM contract test baseline"
```

### Detecting Regressions

Create a comparison script `tests/llm_contracts/compare_results.py`:

```python
#!/usr/bin/env python3
"""Compare contract test results against baseline."""

import json
import sys
from pathlib import Path


def load_results(path: str) -> dict:
    """Load promptfoo results JSON."""
    with open(path) as f:
        return json.load(f)


def calculate_accuracy(results: dict) -> float:
    """Calculate overall test accuracy."""
    total = len(results['results'])
    passed = sum(1 for r in results['results'] if r['pass'])
    return passed / total if total > 0 else 0.0


def calculate_intent_accuracy(results: dict) -> float:
    """Calculate intent classification accuracy."""
    intent_tests = [r for r in results['results'] if 'intent' in r['description'].lower()]
    total = len(intent_tests)
    passed = sum(1 for r in intent_tests if r['pass'])
    return passed / total if total > 0 else 0.0


def calculate_hallucination_rate(results: dict) -> float:
    """Calculate hallucination test failure rate."""
    halluc_tests = [r for r in results['results'] if 'hallucination' in r['description'].lower()]
    total = len(halluc_tests)
    if total == 0:
        return 0.0
    failed = sum(1 for r in halluc_tests if not r['pass'])
    return failed / total


def compare_baseline(new_results_path: str, baseline_path: str = 'baseline.json'):
    """Compare new results against baseline."""
    baseline = load_results(baseline_path)
    new_results = load_results(new_results_path)

    # Calculate metrics
    baseline_metrics = {
        'overall_accuracy': calculate_accuracy(baseline),
        'intent_accuracy': calculate_intent_accuracy(baseline),
        'hallucination_rate': calculate_hallucination_rate(baseline)
    }

    new_metrics = {
        'overall_accuracy': calculate_accuracy(new_results),
        'intent_accuracy': calculate_intent_accuracy(new_results),
        'hallucination_rate': calculate_hallucination_rate(new_results)
    }

    # Check for regressions
    regressions = []

    if new_metrics['overall_accuracy'] < baseline_metrics['overall_accuracy'] - 0.05:
        regressions.append(
            f"Overall accuracy dropped: {baseline_metrics['overall_accuracy']:.1%} → {new_metrics['overall_accuracy']:.1%}"
        )

    if new_metrics['intent_accuracy'] < baseline_metrics['intent_accuracy'] - 0.05:
        regressions.append(
            f"Intent accuracy dropped: {baseline_metrics['intent_accuracy']:.1%} → {new_metrics['intent_accuracy']:.1%}"
        )

    if new_metrics['hallucination_rate'] > baseline_metrics['hallucination_rate'] + 0.01:
        regressions.append(
            f"Hallucination rate increased: {baseline_metrics['hallucination_rate']:.1%} → {new_metrics['hallucination_rate']:.1%}"
        )

    # Report results
    print("=" * 60)
    print("LLM CONTRACT TEST COMPARISON")
    print("=" * 60)
    print(f"Baseline: {baseline_path}")
    print(f"New:      {new_results_path}")
    print()
    print(f"Overall Accuracy:    {baseline_metrics['overall_accuracy']:.1%} → {new_metrics['overall_accuracy']:.1%}")
    print(f"Intent Accuracy:     {baseline_metrics['intent_accuracy']:.1%} → {new_metrics['intent_accuracy']:.1%}")
    print(f"Hallucination Rate:  {baseline_metrics['hallucination_rate']:.1%} → {new_metrics['hallucination_rate']:.1%}")
    print()

    if regressions:
        print("⚠️  REGRESSIONS DETECTED:")
        for r in regressions:
            print(f"  - {r}")
        print()
        print("❌ Contract tests FAILED - regressions detected")
        sys.exit(1)
    else:
        if new_metrics['overall_accuracy'] >= 0.95:
            print("✅ Contract tests PASSED - no regressions")
            print(f"   Accuracy: {new_metrics['overall_accuracy']:.1%} (target: ≥95%)")
            sys.exit(0)
        else:
            print("⚠️  Contract tests passed baseline comparison")
            print(f"   BUT accuracy {new_metrics['overall_accuracy']:.1%} < 95% target")
            print("   Consider improving prompts or model")
            sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python compare_results.py <new_results.json> [baseline.json]")
        sys.exit(1)

    new_path = sys.argv[1]
    baseline_path = sys.argv[2] if len(sys.argv) > 2 else 'baseline.json'

    compare_baseline(new_path, baseline_path)
```

**Usage**:

```bash
# Run tests and compare to baseline
npx promptfoo eval -o new_results.json
python compare_results.py new_results.json baseline.json
```

---

## CI/CD Integration

### GitHub Actions Workflow

Add to `.github/workflows/llm-contract-tests.yml`:

```yaml
name: LLM Contract Tests

on:
  # Run on demand
  workflow_dispatch:

  # Run weekly (every Monday at 9am)
  schedule:
    - cron: '0 9 * * 1'

  # Run on PR to main
  pull_request:
    branches: [main]
    paths:
      - 'prt_src/llm_*.py'
      - 'tests/llm_contracts/**'

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Ollama
        run: |
          curl -fsSL https://ollama.com/install.sh | sh
          ollama serve &
          sleep 5

      - name: Pull model
        run: |
          # Use fast model for CI (llama3.2:3b is ~2GB, much faster)
          ollama pull llama3.2:3b

      - name: Install promptfoo
        run: npm install -g promptfoo

      - name: Run contract tests
        run: |
          cd tests/llm_contracts
          # Override provider to use faster model
          npx promptfoo eval \
            -c promptfooconfig.yaml \
            -p ollama:llama3.2:3b \
            -o results.json

      - name: Compare against baseline
        run: |
          cd tests/llm_contracts
          python compare_results.py results.json baseline.json

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: contract-test-results
          path: tests/llm_contracts/results.json
```

**Note**: Using `llama3.2:3b` in CI for speed. Your baseline should be created with the same model you use in CI.

---

## Best Practices

### 1. Start Small, Grow Test Suite

```
Phase 0: 5 critical tests (intent classification)
Phase 3: 20 tests (parameters, edge cases)
Phase 7: 60+ tests (comprehensive coverage)
```

### 2. Test Categories

Organize tests by category:

```yaml
tests:
  # CRITICAL: Intent classification
  - description: '[CRITICAL] Search intent'
    ...

  # CRITICAL: No hallucinations
  - description: '[CRITICAL] No fake names'
    ...

  # IMPORTANT: Parameter extraction
  - description: '[IMPORTANT] Tag extraction'
    ...

  # NICE-TO-HAVE: Edge cases
  - description: '[EDGE] Empty query'
    ...
```

### 3. Meaningful Descriptions

```yaml
# Good: Specific, testable
- description: 'Extract tags: tech, python from multi-tag query'

# Bad: Vague
- description: 'Test tags'
```

### 4. Target Metrics

| Metric | Target | Action if Below |
|--------|--------|-----------------|
| Overall accuracy | ≥95% | Improve system prompt |
| Intent accuracy | ≥95% | Add more examples to prompt |
| JSON validity | 100% | Enforce JSON-only output |
| Hallucination rate | 0% | Strengthen "no invention" rules |

### 5. Update Baseline Carefully

Only update baseline when:
- ✅ All tests pass
- ✅ Accuracy ≥ 95%
- ✅ Changes are intentional (prompt improvements)
- ❌ NOT to "fix" failing tests

---

## Troubleshooting

### Tests Fail Intermittently

**Cause**: LLM non-determinism

**Solutions**:
- Lower `temperature` to 0.0 (more consistent)
- Run multiple times, accept 90%+ pass rate
- Use larger model (gpt-oss:20b > llama3.2:3b)

### Tests Timeout

**Cause**: Slow model loading or inference

**Solutions**:
- Set `keep_alive: "30m"` in Ollama
- Preload model: `ollama run gpt-oss:20b "test"`
- Increase timeout in promptfoo config
- Use smaller model for testing

### JSON Assertions Fail

**Cause**: LLM returns text instead of pure JSON

**Fix system prompt**:
```
IMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, just JSON.

Example: {"intent": "search", "parameters": {...}}
```

### Baseline Comparison Errors

**Cause**: Different models or configurations

**Solution**: Ensure consistency:
- Same model (gpt-oss:20b vs llama3.2:3b)
- Same temperature (0.1)
- Same Ollama version
- Same system prompt

---

## Related Documentation

- **[04_Testing_Strategy.md](./04_Testing_Strategy.md)** - Complete testing approach (4 layers)
- **[02_Configuration.md](./02_Configuration.md)** - LLM configuration reference
- **[05_Ollama_Integration.md](./05_Ollama_Integration.md)** - Ollama setup and troubleshooting
- **[03_Implementation_Plan.md](./03_Implementation_Plan.md)** - Phase 3 covers contract testing

**External**:
- [Promptfoo Documentation](https://www.promptfoo.dev/docs/)
- [Promptfoo GitHub](https://github.com/promptfoo/promptfoo)
- [Assertion Types Reference](https://www.promptfoo.dev/docs/configuration/expected-outputs/)

---

## Summary

**Contract testing with Promptfoo enables**:

1. ✅ **Confidence** - Validate LLM produces correct outputs (≥95% accuracy)
2. ✅ **Regression detection** - Catch prompt changes that break parsing
3. ✅ **Safety** - Ensure zero hallucination rate
4. ✅ **Fast feedback** - Tests run in 1-5 minutes (vs 30s per manual test)
5. ✅ **CI integration** - Automated testing before merges

**Testing workflow**:
1. Write tests first (Phase 3)
2. Run: `npx promptfoo eval`
3. Iterate on prompt until ≥95% pass
4. Save baseline: `npx promptfoo eval -o baseline.json`
5. CI runs tests weekly + on prompt changes
6. Compare new results to baseline before accepting changes

This approach gives you confidence that your LLM integration works reliably without manual testing every change!
