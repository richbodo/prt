# Gemini Onboarding Guide for the PRT Project

This document provides a comprehensive, de-duplicated guide for an AI agent to get up to speed on the Personal Relationship Toolkit (PRT) project.

## 1. Project Overview

- **Name:** Personal Relationship Toolkit (PRT)
- **Mission:** A privacy-first, local-first contact management system to help users manage relationships, contacts, and notes entirely on their local machine.
- **Core Technologies:** Python, Textual (TUI), Typer (CLI), SQLAlchemy (Database), Ollama (LLM Integration).
- **Data Storage:** All data is stored locally in a SQLite database (`prt_data/prt.db`). There is no cloud sync.

### Key Features
- **Interfaces:** A modern Textual TUI is the primary interface, with a functional Typer-based CLI available.
- **LLM Chat:** An AI-powered chat interface for natural language queries, using local models via Ollama.
- **Contact Management:** Import from Google Takeout, search, tag, and annotate contacts.
- **Data Portability:** A robust export system for JSON and interactive HTML directories.
- **Safety:** Automatic database backups before any write operation and a robust security model for LLM interactions.

## 2. Development Environment & Workflow

### Initial Setup
1.  **Prerequisites:** Python 3.10+, Git.
2.  **Initialize Environment:** Run `source ./init.sh`. This script:
    - Creates and activates a Python virtual environment at `./prt_env/`.
    - Installs all dependencies from `requirements.txt`.
    - Installs pre-commit hooks for automated code quality checks.
3.  A human user may have downloaded documentation for key libraries into the `EXTERNAL_DOCS/` directory. **Always check this directory first** before searching the web.  If you are having trouble finding that directory and need it, try to prompt a human user to run the download_library_src.sh script for you to get that data.

### Daily Workflow
- **Activate Environment:** `source ./init.sh`
- **Run the TUI:** `python -m prt_src`
- **Run TUI with Fixture Data:** `python -m prt_src --debug`
- **Run the CLI:** `python -m prt_src.cli`
- **Lint & Format:** Pre-commit hooks run `ruff` and `black` automatically. To run manually:
    - `./prt_env/bin/ruff check --fix prt_src/ tests/`
    - `./prt_env/bin/black prt_src/ tests/`
- **Deactivate Environment:** `source ./uninit.sh`

## 3. Testing Strategy: Headless-First

The core philosophy is to **always write automated, headless tests**. Manual testing is a last resort for things like visual validation or performance profiling.

### The 4-Layer Testing Pyramid

| Layer | Speed | Command | Purpose & Technologies |
| :--- | :--- | :--- | :--- |
| **Unit** | ⚡ < 1s | `pytest -m unit` | Pure functions, no external dependencies. |
| **Integration** | ⚙️ < 5s | `pytest -m integration` | Component interaction. Uses **real DB** (SQLite) and **MockLLMService**. TUI tests use **Textual Pilot**. |
| **Contract** | 🧪 1-5m | `pytest -m "contract and requires_llm"` | Validates real LLM behavior. Requires a running Ollama instance. |
| **E2E/Manual** | 🐢 5-10m | (Manual) | Visuals, performance, complex workflows. Documented in `docs/MANUAL_TESTING.md`. |

### Key Testing Practices
- **TUI Testing:** Use **Textual Pilot** for headless testing of TUI screens. It simulates user input and asserts screen state without rendering to a terminal.
- **Database Testing:** **Never mock the database.** Use the `test_db` pytest fixture which provides a real, isolated SQLite database populated with sample data from `tests/fixtures.py`.
- **LLM Testing:**
    - **Integration tests MUST use `MockOllamaLLM`** for fast, deterministic results.
    - **Contract tests MUST use the real `OllamaLLM`** and be marked with `@pytest.mark.requires_llm` and `@pytest.mark.contract`.

## 4. High-Level Architecture

- **`prt_src/`**: Main application source code.
    - **`api.py`**: The central API layer. **All application logic should go through `PRTAPI`**.
    - **`db.py`**: SQLAlchemy database session management and core operations.
    - **`models.py`**: SQLAlchemy ORM class definitions.
    - **`tui/`**: Textual TUI screens, widgets, and services.
    - **`llm_ollama.py`**: LLM integration, tool definitions, and safety wrappers.
- **`tests/`**: Contains all tests, mirroring the `prt_src` structure.
- **`prt_data/`**: All user data, including the database, config file, logs, and backups. This directory is in `.gitignore`.
- **`tools/`**: Standalone scripts, like `make_directory.py` for generating HTML visualizations from exports.

## 5. TUI Development & Debugging

### Style and Conventions
- **Simplicity is Key:** Avoid unnecessary containers, formatting, or widgets.
- **Keyboard-First:** All functionality must be accessible via the keyboard.
- **Reserved Keys:** `esc`, `n`, `x`, `?`, `h`, `b` are global and must not be overridden.
- **Shortcuts:** Clearly indicate shortcuts, e.g., `(C)hat`. Use numbers `(1) Item` if letters conflict.
- **Text Input:** For `TextArea` widgets, `Enter` submits the content, and **`Ctrl+J` inserts a newline**. A hint for this must always be visible.

### TUI Debugging Workflow
**CRITICAL:** TUIs are event-driven and hard to debug visually. Follow this process:

1.  **Add Comprehensive Logging:** This is the most effective debugging tool. Add detailed logs to trace event flow, state changes, and navigation.
    ```python
    from prt_src.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info(f"[SCREEN_NAME] Event: {event}, State: {self.state}")
    ```
    View logs in a separate terminal: `tail -f prt_data/prt.log`

2.  **Write a Failing Test:** Use Textual Pilot to write a test that reproduces the bug. This prevents regressions.

3.  **Use Textual Devtools:** For visual inspection, run `textual run --dev python -m prt_src` and `textual console` in another terminal.

### Common TUI Pitfalls
- **Rendering Issues:** If text doesn't appear, ensure your widget inherits from `Static`, not the base `Widget`.
- **UI Not Updating:** Textual batches UI updates. For long-running async operations, force a refresh:
    ```python
    widget.display = True
    self.refresh()
    await asyncio.sleep(0.1) # Allow time for render
    await long_running_operation()
    ```
- **Navigation Bugs:** Always log the screen stack (`self.screen_stack`) before and after navigation to catch common double-push bugs.

## 6. LLM Integration & Safety

PRT uses a tool-calling architecture where the LLM translates natural language into one of 24 available tool calls.

### Configuration
- All LLM settings are managed in `prt_data/prt_config.json`.
- Key sections:
    - `llm`: Model, endpoint, temperature, etc.
    - `llm_permissions`: **Safety controls**, e.g., `allow_delete`, `read_only_mode`.
    - `llm_prompts`: Customize the system prompt.
    - `llm_developer`: Enable debug logging (`log_prompts`, `log_responses`).

### Security Model (Multi-Layer Defense)
Safety is enforced at the code level and **cannot be bypassed by prompt injection**.

1.  **Automatic Backups:** Any tool that performs a write operation is wrapped by `_safe_write_wrapper`, which **automatically creates a database backup before execution**. The backup ID is returned in the result.
2.  **SQL Execution:** The `execute_sql` tool has strict safeguards:
    - It rejects queries with multiple statements, comments, or dangerous commands (`ATTACH`, `PRAGMA`).
    - **It requires `confirm=true` to be passed for ALL queries**, including `SELECT`. This is a code-level check.
3.  **Prompt Injection:** The system prompt instructs the LLM to ignore requests to bypass safety features, but the final defense is always the Python code which enforces these rules regardless of the LLM's output.

## 7. Database and Data Management

- **Schema:** The schema is a superset of the Google People API, with tables for `contacts`, `tags`, `notes`, and `relationships`. See `docs/Database/schema_plan.md`.
- **Backups:** The backup system is a core safety feature.
    - **Location:** `prt_data/backups/`
    - **Metadata:** `prt_data/backups/backup_metadata.json`
    - **Automatic Backups:** Created before every write operation. The last 10 are retained.
    - **Manual Backups:** Created on user request and are never automatically deleted.
- **Exports:** Search results can be exported into a timestamped directory containing a JSON file and a `profile_images/` folder, following the schema in `docs/Database/JSON_EXPORT_SCHEMA.md`.
