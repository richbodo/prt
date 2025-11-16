# Developer Environment & Workflow Guide

This guide consolidates everything you need to get productive quickly on PRT. It covers the daily environment workflow, shortcuts for AI-assisted development, and quick Git references. It is designed to complement the historical/legacy documents that still live in the repository.

## 1. Prerequisites

| Requirement | Notes |
| --- | --- |
| Python 3.10+ | macOS ships with an older Python; install via [Homebrew](https://brew.sh) or `pyenv`. |
| Git | Required for version control. `xcode-select --install` on macOS installs Git. |
| Homebrew (macOS) / apt (Debian/Ubuntu) | Needed for system packages. |
| Optional: [Cursor](https://cursor.sh), OpenAI Codex, Claude Code | Works great alongside this repository - used in development |
| LLM Interface | We are using ollama various LLM models (gptoss20b, vaultgemma), so you will need to get one of those running and available to use the chat feature |

### Download and install a model that works

ollama pull gpt-oss:20b
ollama run gpt-oss:20b

Then test it in the ollama app.  You're good to go.

Note: LLMs and agents will work a lot better for you if they have access to local copies of all the library code and docs they need.  The script "download_library_src.sh" in the root of this project will create an EXTERNAL_DOCS folder with all the libraries LLMs will commonly benefit from.  That folder is gitignored.  The claude.md file references the EXTERNAL_DOCS folder.

## 2. Start-of-Day Setup

1. Open a shell in the project root (`prt`).
2. Run `source ./init.sh` – Sets up/activates the `prt_env` virtual environment in your current shell.
3. When the environment finishes:
   * `(prt_env)` prefix should be in your prompt.
   * Pre-commit hooks are installed.
   * Dependencies from `requirements.txt` are available.

If you see activation issues, run `source prt_env/bin/activate` manually. The init scripts verify installation by importing `textual`, `sqlalchemy`, and `typer`.

## 3. End-of-Day Cleanup

* `source ./uninit.sh` – Deactivates the environment in your current shell and clears old SQLCipher variables.

If your shell still shows `(prt_env)`, run `deactivate` manually.

## 4. Daily Command Cheat Sheet

| Intent | Command |
| --- | --- |
| Launch TUI | `python -m prt_src` |
| Use CLI instead of TUI | `python -m prt_src --cli` |
| Run classic CLI | `python -m prt_src --classic` |
| Debug TUI with fixtures | `python -m prt_src --debug` |
| System diagnostic info | `python -m prt_src prt-debug-info` |
| List available AI models | `python -m prt_src list-models` |
| **Fast CI tests (recommended)** | `./scripts/run-ci-tests.sh` |
| **Full local test suite** | `./scripts/run-local-tests.sh` |
| Unit tests only (< 1 sec) | `./prt_env/bin/pytest -m unit` |
| Integration tests only (< 5 sec) | `./prt_env/bin/pytest -m integration` |
| Quick tests (first failure) | `./prt_env/bin/pytest tests/ -x` |
| Full test suite (verbose) | `./prt_env/bin/pytest tests/ -v` |
| Coverage report | `./prt_env/bin/pytest tests/ --cov=prt_src --cov-report=html --cov-report=term` |
| Lint | `./prt_env/bin/ruff check prt_src/ tests/` |
| Auto-fix formatting | `./prt_env/bin/ruff check --fix prt_src/ tests/ && ./prt_env/bin/black prt_src/ tests/` |
| Clean caches/builds | `find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; find . -type f -name "*.pyc" -delete` |
| Check outdated packages | `./prt_env/bin/pip list --outdated` |
| Run pre-commit everywhere | `./prt_env/bin/pre-commit run --all-files` |

### CLI Testing & Debugging Commands

The CLI is excellent for testing and debugging PRT functionality:

| Purpose | Command | Notes |
| --- | --- | --- |
| **System Health Check** | `python -m prt_src prt-debug-info` | Shows system status, database stats, LLM connectivity |
| **Test AI Chat** | `python -m prt_src --cli --chat "count contacts"` | Quick AI functionality test |
| **Complex AI Queries** | `python -m prt_src --cli --chat "make a directory of contacts with first name Rich"` | Test advanced AI operations |
| **Model Selection** | `python -m prt_src --model gpt-oss-20b --chat "find friends"` | Test specific AI models |
| **Interactive Chat** | `python -m prt_src --chat="" --model mistral-7b-instruct` | Enter interactive AI chat mode |
| **Database Status** | `python -m prt_src db-status` | Check database connectivity and schema |
| **Connection Test** | `python -m prt_src test-db` | Test database connection and credentials |
| **Available Models** | `python -m prt_src list-models` | List all available AI models with status |

**Pro Tips for Development:**
- Use `prt-debug-info` first when debugging issues
- Test AI functionality with simple queries before complex ones
- Use `--debug` flag to work with sample data safely
- CLI chat mode is perfect for testing tool chaining and AI responses

> **Note:** Use the test scripts (`./scripts/run-ci-tests.sh` and `./scripts/run-local-tests.sh`) for daily development. See `docs/RUNNING_TESTS.md` for complete testing guidance.

> **Cursor/LLM tip:** Paste the table above into your prompt or keep it pinned in a scratchpad so Codex/Claude can cite the correct commands for you.

## 5. Testing Philosophy: Headless First

**ALWAYS write automated, headless tests wherever possible.**

This applies to both humans and LLMs working on PRT. The project has comprehensive headless testing infrastructure:
- **TUI testing**: Use Textual Pilot to simulate user interactions without rendering to terminal
- **LLM testing**: Use fixtures and mocks; skip real LLM calls in CI with `@pytest.mark.skipif`
- **Database testing**: Use real SQLite with fixtures (no mocking needed - SQLite is fast)

### The 4-Layer Testing Pyramid

Tests are organized in layers from fast/frequent (bottom) to slow/rare (top):

1. **Unit Tests** ⚡ (< 1 sec) - Pure functions, formatters, no external dependencies
   - `./prt_env/bin/pytest -m unit`
   - Examples: `tests/unit/test_results_formatter.py`, `tests/unit/test_selection_service.py`

2. **Integration Tests** ⚙️ (< 5 sec) - Component interactions, workflows, screen navigation
   - `./prt_env/bin/pytest -m integration`
   - Examples: `tests/test_home_screen.py`, `tests/integration/test_llm_one_query.py`

3. **Contract Tests** 🧪 (1-5 min) - LLM behavior validation with Promptfoo
   - `npx promptfoo@latest eval -c tests/llm_contracts/promptfooconfig.yaml`

4. **Manual Tests** 🐢 (5-10 min) - Visual validation, performance, accessibility
   - See `docs/MANUAL_TESTING.md` for specific scenarios

### Key Testing Resources

- **🚀 Daily Testing Guide**: `docs/RUNNING_TESTS.md` - **Start here** for test execution, CI/CD patterns, troubleshooting
- **Comprehensive Strategy**: `docs/TESTING_STRATEGY.md` - Complete testing strategy, examples, best practices
- **TUI Testing**: `EXTERNAL_DOCS/textual/docs/guide/testing.md` - Official Textual testing patterns
- **TUI Dev Tips**: `docs/TUI/TUI_Dev_Tips.md` - PRT-specific patterns and debugging
- **Manual Testing**: `docs/MANUAL_TESTING.md` - Scenarios requiring manual testing
- **Test Fixtures**: `tests/fixtures.py` - Sample data (SAMPLE_CONTACTS, get_fixture_spec)

### Quick Examples

**TUI Test with Pilot (headless)**:
```python
async def test_home_screen_navigation(pilot_screen):
    """Test navigation using Textual Pilot."""
    async with pilot_screen(HomeScreen) as pilot:
        await pilot.press("h")  # Press 'h' to navigate to help
        assert isinstance(pilot.app.screen, HelpScreen)
```

**LLM Integration Test (skipped in CI)**:
```python
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_count_contacts(test_db):
    api = PRTAPI(config=test_db_config)
    llm = OllamaLLM(api=api)
    response = llm.chat("How many contacts do I have?")
    assert "7" in response or "seven" in response.lower()
```

### When Manual Testing Is Required

See `docs/MANUAL_TESTING.md` for full list. Common cases:
- Visual regression (colors, alignment, responsive layout)
- Performance profiling (memory usage, render time)
- Accessibility testing (screen readers, keyboard-only navigation)
- Platform-specific rendering (different terminals)

## 6. Git Quick Reference

| Task | Command |
| --- | --- |
| See status | `git status -sb` |
| Stage files | `git add path/to/file` |
| Commit | `git commit -m "Meaningful message"` |
| Amend last commit | `git commit --amend` (avoid after pushing) |
| Undo local file changes | `git restore path/to/file` |
| Unstage a file | `git restore --staged path/to/file` |
| View diff | `git diff` (unstaged) / `git diff --staged` |
| Discard tracked/untracked files | `git clean -fd` (dangerous – double check!) |
| Create topic branch | `git checkout -b feature/name` |
| Pull latest | `git pull --rebase origin main` |

## 7. Recovering a Broken Environment

1. `source ./uninit.sh`
2. `rm -rf prt_env`
3. Re-run `source ./init.sh`
4. If pip installs fail, confirm Homebrew/apt availability and rerun.

For persistent issues, check `requirements.txt` for pinned versions and install manually inside the venv.

## 8. Documentation Map & Freshness

| Doc | Status | Why you'd read it |
| --- | --- | --- |
| `README.md` | USE | High-level project overview and links into the doc set. |
| `docs/DEV_SETUP.md` | USE | (This file) Day-to-day workflow, Git tips, testing cheat sheet. |
| `docs/RUNNING_TESTS.md` | ✅ NEW | **Daily test execution guide** - CI/CD patterns, scripts, troubleshooting. |
| `docs/TESTING_STRATEGY.md` | USE | **Canonical testing guide** - 4-layer pyramid, examples, best practices. |
| `docs/MANUAL_TESTING.md` | USE | Scenarios requiring manual testing (visual, performance, etc). |
| `docs/TUI/TUI_Dev_Tips.md` | USE | TUI-specific patterns, debugging, common issues. |
| `docs/TUI/Chat_Screen_Testing_Strategy.md` | USE | LLM-powered UI testing strategy. |
| `CLAUDE.md` | USE | LLM instructions - includes testing philosophy, debugging patterns. |
| `docs/INSTALL.md` | NEEDS WORK | Legacy SQLCipher install steps. Prefer the quick setup above. |
| `docs/ENCRYPTION_IMPLEMENTATION.md` | NEEDS WORK | Design discussion for future encryption work. |
| `docs/TUI_Specification.md` | NEEDS WORK | Requirements and flows for the modern TUI. |
| `docs/TUI_Key_Bindings.md` | NEEDS WORK | Comprehensive list of TUI shortcuts for manual testing. |
| `docs/TUI/DEBUGGING/TEXTUAL_DEBUG_WORKFLOW.md` | NEEDS WORK | Automated TUI debugging system with visual analysis. |
| `ROADMAP.md` | USE | High-level milestone planning. |

## 10. Handy Snippets

```bash
# Run lint + tests in one go
./prt_env/bin/ruff check prt_src/ tests/ && ./prt_env/bin/python -m pytest tests/

### CLI for Troubleshooting

# Quick system health check
python -m prt_src prt-debug-info

# Test basic database connectivity
python -m prt_src db-status

# Test AI functionality
python -m prt_src --cli --chat "how many contacts do I have?"

# Check what models are available
python -m prt_src list-models

# Test with debug data (safe)
python -m prt_src --debug prt-debug-info

# Run setup if needed
python -m prt_src --setup

# Legacy interactive mode for import operations
python -m prt_src --classic
```

## 11. TUI Testing & Debugging

### **Headless Testing with Textual Pilot**

PRT uses Textual Pilot for automated, headless TUI testing. This allows testing screen navigation, key presses, and widget interactions without rendering to a terminal.

**Quick Example**:
```python
async def test_home_screen_navigation(pilot_screen):
    """Test navigation using Textual Pilot."""
    async with pilot_screen(HomeScreen) as pilot:
        # Simulate pressing 'h' key
        await pilot.press("h")

        # Verify help screen is now active
        assert isinstance(pilot.app.screen, HelpScreen)
```

**Running TUI Tests**:
```bash
# Run all TUI integration tests
./prt_env/bin/pytest tests/test_*_screen.py -v

# Run specific TUI test
./prt_env/bin/pytest tests/test_home_screen.py::test_navigation -v
```

**Current TUI Tests** (examples to follow):
- `tests/test_home_screen.py` - Home screen navigation
- `tests/test_help_screen.py` - Help screen rendering
- `tests/test_chat_navigation.py` - Chat screen modes and scrolling
- `tests/test_phase2_screens.py` - Search and Settings screens

### **Debugging TUI Issues**

**Primary Tools**:
1. **Logging** - Add comprehensive logging to trace event flow (see `docs/TUI/TUI_Dev_Tips.md`)
2. **Pilot** - Write failing test to reproduce issue, then fix
3. **Textual Devtools** - Use `textual run --dev` for visual debugging

**Watch Logs** (2-terminal setup):
```bash
# Terminal 1: Watch logs in real-time
tail -f prt_data/prt.log | grep '\[SCREEN\]'

# Terminal 2: Run TUI
./prt_env/bin/python -m prt_src
```

**For Complete TUI Development Guidance**:
- **Testing**: `docs/TESTING_STRATEGY.md` - Complete guide with Pilot examples
- **Debugging**: `docs/TUI/TUI_Dev_Tips.md` - Logging patterns, common issues, Pilot debugging
- **Textual Docs**: `EXTERNAL_DOCS/textual/docs/guide/testing.md` - Official Textual testing guide


