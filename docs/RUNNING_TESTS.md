# Running Tests - PRT Test Execution Guide

This guide explains how to run tests effectively in the PRT project, covering local development, CI environments, and troubleshooting.

## Quick Reference

### Daily Development
```bash
# Fast CI tests (unit + integration) - run before committing
./scripts/run-ci-tests.sh

# Full local test suite (with LLM tests if available)
./scripts/run-local-tests.sh

# Specific test categories
./prt_env/bin/pytest -m unit          # Unit tests only
./prt_env/bin/pytest -m integration   # Integration tests only
./prt_env/bin/pytest -m e2e           # End-to-end tests
```

### Before Merging
```bash
# Run the same tests that CI will run
./scripts/run-ci-tests.sh

# Should complete in < 2 minutes
```

## Test Categories

### 🧪 Unit Tests (< 1 second each)
- **Purpose**: Test deterministic components without external dependencies
- **When to run**: After every change, before committing
- **Command**: `./prt_env/bin/pytest -m unit`
- **Count**: ~78 tests

**What they test:**
- Pure functions and data transformers
- Formatters and parsers
- Configuration handlers
- Mock-based service components

### 🔧 Integration Tests (< 5 seconds total)
- **Purpose**: Test component interactions with mocked external dependencies
- **When to run**: Before committing, in CI
- **Command**: `./prt_env/bin/pytest -m integration`
- **Count**: ~211 tests

**What they test:**
- TUI screen navigation and workflows
- Database operations with test fixtures
- API interactions with MockLLMService
- Service integration patterns

### 🎭 End-to-End Tests (< 10 seconds total)
- **Purpose**: Test complete user workflows
- **When to run**: Before major releases, in comprehensive CI
- **Command**: `./prt_env/bin/pytest -m e2e`

**What they test:**
- Setup workflows and error handling
- Complete user interaction paths
- Application startup and shutdown

### ⚡ Performance Tests
- **Purpose**: Benchmark query speed and resource usage
- **When to run**: When optimizing, before releases
- **Command**: `./prt_env/bin/pytest -m performance`

**What they test:**
- Database query optimization
- Memory usage patterns
- Tool chain performance
- Index usage verification

### 🤖 LLM Contract Tests (1-5 minutes)
- **Purpose**: Validate real LLM behavior and tool calling
- **When to run**: Nightly, when LLM code changes
- **Command**: `./prt_env/bin/pytest -m contract`
- **Requires**: Ollama with gpt-oss:20b model

**What they test:**
- Real LLM tool calling functionality
- Response format validation
- End-to-end LLM workflows

## CI/CD Test Strategy

### Fast CI Pipeline (Pull Requests)
```yaml
Triggers: PR, push to main/develop
Runtime: < 2 minutes
Tests: Unit + Integration (mocked)
Purpose: Quick feedback for developers
```

**Command equivalent:**
```bash
./prt_env/bin/pytest -m "unit or integration" --timeout=120
```

### Comprehensive CI Pipeline (Nightly/Releases)
```yaml
Triggers: Schedule (2 AM), releases, manual
Runtime: < 15 minutes
Tests: All categories including LLM contract tests
Purpose: Full validation
```

**Command equivalent:**
```bash
# Without LLM
./prt_env/bin/pytest -m "unit or integration or e2e or performance" --timeout=600

# With LLM (requires Ollama)
./prt_env/bin/pytest --timeout=600 tests/
```

## Local Development Patterns

### Before Committing
```bash
# 1. Run fast CI tests
./scripts/run-ci-tests.sh

# 2. If working on LLM features, run contract tests
./prt_env/bin/pytest -m contract -v

# 3. For UI changes, run E2E tests
./prt_env/bin/pytest -m e2e -v
```

### When Debugging
```bash
# Single test with full output
./prt_env/bin/pytest tests/test_specific.py::TestClass::test_method -vs

# Test with debugging info
./prt_env/bin/pytest tests/test_failing.py -vvs --tb=long

# Run until first failure
./prt_env/bin/pytest tests/ -x
```

### Performance Testing
```bash
# Run all performance tests
./prt_env/bin/pytest -m performance -v

# Specific performance test with output
./prt_env/bin/pytest tests/test_contacts_with_images_performance.py -v -s
```

## Test Environment Setup

### Prerequisites
```bash
# 1. Set up virtual environment
source ./init.sh

# 2. Verify environment
python --version  # Should be 3.11+
pytest --version
```

### LLM Testing Setup
```bash
# 1. Install Ollama
# Visit: https://ollama.com/

# 2. Pull required model
ollama pull gpt-oss:20b

# 3. Verify setup
ollama list
curl http://localhost:11434/api/version
```

### Database Testing
The test suite uses isolated SQLite databases that are automatically created and cleaned up. No additional setup required.

## Troubleshooting Common Issues

### Virtual Environment Issues
```bash
# Problem: Tests run but can't find modules
# Solution: Ensure virtual environment is activated
source ./init.sh
which python  # Should point to prt_env/bin/python
```

### Test Failures After Git Pull
```bash
# Problem: Tests fail after pulling new changes
# Solution: Update dependencies and rebuild fixtures
source ./init.sh
pip install -r requirements.txt
./prt_env/bin/pytest tests/test_fixture_isolation.py -v
```

### LLM Tests Skip or Fail
```bash
# Problem: LLM tests are skipped
# Solution: Check Ollama setup
ollama --version
ollama list  # Should show gpt-oss:20b
curl http://localhost:11434/api/version

# Problem: LLM tests timeout
# Solution: Increase timeout for contract tests
./prt_env/bin/pytest -m contract --timeout=600
```

### Database Lock Errors
```bash
# Problem: Database is locked errors during tests
# Solution: Clean up test databases
rm -f tests/prt_data/*.db
./prt_env/bin/pytest tests/test_db.py -v
```

### Memory Issues During Tests
```bash
# Problem: Out of memory errors
# Solution: Run tests in smaller batches
./prt_env/bin/pytest tests/unit/ -v
./prt_env/bin/pytest tests/integration/ -v
```

## Test Data and Fixtures

### Test Database
- Location: `tests/prt_data/test_fixtures.db`
- Content: 6 sample contacts with images, 8 tags, 6 notes
- Reset: Automatic for each test

### Fixture Data
```bash
# View fixture data
cd tests && python fixtures.py

# Extract profile images from fixtures
cd utils && python extract_profile_images.py
```

### Mock Services
- **MockLLMService**: Provides deterministic LLM responses
- **Test fixtures**: Realistic sample data for all models
- **Isolated databases**: Each test gets a clean database state

## Coverage Reporting

### Generate Coverage Report
```bash
# HTML report
./prt_env/bin/pytest --cov=prt_src --cov-report=html tests/

# Terminal report
./prt_env/bin/pytest --cov=prt_src --cov-report=term-missing tests/

# View HTML report
open htmlcov/index.html
```

### Coverage Targets
- **Unit tests**: > 80% coverage
- **Integration tests**: Cover critical workflows
- **Combined**: > 70% overall coverage

## Performance Benchmarks

### Expected Performance
- **Unit tests**: < 1 second each
- **Integration tests**: < 5 seconds total
- **E2E tests**: < 10 seconds total
- **CI pipeline (fast)**: < 2 minutes
- **CI pipeline (comprehensive)**: < 15 minutes

### Monitoring Performance
```bash
# Time test execution
time ./scripts/run-ci-tests.sh

# Profile specific tests
./prt_env/bin/pytest tests/test_performance.py -v --tb=short
```

## Writing New Tests

### Test Organization
```python
# Mark tests appropriately
@pytest.mark.unit
def test_pure_function():
    """Test pure function without external dependencies."""
    pass

@pytest.mark.integration
def test_service_interaction(test_db):
    """Test service interaction with test database."""
    pass

@pytest.mark.e2e
async def test_user_workflow():
    """Test complete user workflow end-to-end."""
    pass
```

### Naming Conventions
- **Unit**: `test_function_name_behavior`
- **Integration**: `test_component_interaction_scenario`
- **E2E**: `test_user_workflow_description`

### Best Practices
1. **Isolation**: Each test should be independent
2. **Performance**: Keep unit tests under 1 second
3. **Mocking**: Use MockLLMService for LLM tests
4. **Cleanup**: Use fixtures for database setup/teardown
5. **Markers**: Always mark tests with appropriate categories

---

**For other testing documentation:**
- **[TESTING_STRATEGY.md](TESTING_STRATEGY.md)** - Comprehensive testing strategy and patterns
- **[MANUAL_TESTING.md](MANUAL_TESTING.md)** - Manual testing scenarios when headless testing isn't possible
- **[TUI/TUI_Dev_Tips.md](TUI/TUI_Dev_Tips.md)** - TUI-specific testing patterns and debugging
- **[TUI/Chat_Screen_Testing_Strategy.md](TUI/Chat_Screen_Testing_Strategy.md)** - Detailed chat screen testing approach
