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
| Run classic CLI | `python -m prt_src --classic` |
| Debug TUI with fixtures | `python -m prt_src --debug` |
| Quick tests | `./prt_env/bin/python -m pytest tests/ -x` |
| Full tests | `./prt_env/bin/python -m pytest tests/ -v` |
| Coverage report | `./prt_env/bin/python -m pytest tests/ --cov=prt_src --cov-report=html --cov-report=term` |
| Lint | `./prt_env/bin/ruff check prt_src/ tests/` |
| Auto-fix formatting | `./prt_env/bin/ruff check --fix prt_src/ tests/ && ./prt_env/bin/black prt_src/ tests/` |
| Clean caches/builds | `find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; find . -type f -name "*.pyc" -delete` |
| Check outdated packages | `./prt_env/bin/pip list --outdated` |
| Run pre-commit everywhere | `./prt_env/bin/pre-commit run --all-files` |

> **Cursor/LLM tip:** Paste the table above into your prompt or keep it pinned in a scratchpad so Codex/Claude can cite the correct commands for you.

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

| Doc | Status | Why you’d read it |
| --- | --- | --- |
| `README.md` | USE | High-level project overview and links into the doc set. |
| `docs/DEV_SETUP.md` | USE | (This file) Day-to-day workflow, Git tips, AI helper guidance. |
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

# Snapshot database status from the CLI
python -m prt_src db-status

# Import Google Takeout export interactively - many things are not in the TUI yet
python -m prt_src --classic
```

## 11. TUI Debugging System

### **Automated Textual Debug Workflow**

WORK IN PROGRESS - WORTH A TRY

For TUI development and debugging, use the comprehensive debug system in `docs/TUI/DEBUGGING/`:

```bash
# Setup environment first (always start here)
source ./init.sh

# Setup (2-terminal workflow)
# Terminal 1: Start debug console
textual console --port 7342 -v

# Terminal 2: Run TUI with debugging
textual run --dev --port 7342 python -m prt_src
```

### **Interactive Debug Features**
When the TUI is running with debug mode:
- **`d`** - Toggle visual debug borders (containers, scrollable regions)
- **`l`** - Log comprehensive layout analysis with widget tree
- **`n`** - Test notification system with different severity levels
- **`s`** - Trigger screenshot capture (requires screenpipe integration)
- **`r`** - Test responsive behavior at multiple screen sizes

### **Debug Capabilities**
- **Layout Analysis**: Complete widget tree with size/style information
- **Issue Detection**: Automatic overflow, sizing, and responsive problem identification
- **Visual Debugging**: CSS borders and highlights for layout visualization
- **Performance Monitoring**: Render time tracking and widget count analysis
- **Screenpipe Integration**: Visual state capture correlated with app state (manually start screenpipe and guide LLMs to grab screenshots)

### **When to Use TUI Debugging**
- Layout issues (widgets not appearing, incorrect sizing)
- Container and scrolling problems
- Screen resizing and responsive behavior issues
- Performance optimization and bottleneck identification
- Visual regression testing during development

### **TUI DEBUG Documentation References**
- **Main Guide**: `docs/TUI/DEBUGGING/TEXTUAL_DEBUG_WORKFLOW.md`
- **Demo App**: `docs/TUI/DEBUGGING/textual_debug_demo.py`
- **Development Tips**: `docs/TUI/TUI_Dev_Tips.md`
- **Common Patterns**: Widget inheritance, CSS debugging, container management


