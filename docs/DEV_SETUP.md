# Developer Environment & Workflow Guide

This guide consolidates everything you need to get productive quickly on PRT. It covers the daily environment workflow, recommended Make targets, shortcuts for AI-assisted development, and quick Git references. It is designed to complement the historical/legacy documents that still live in the repository.

> **Tip:** If you prefer sourcing shell scripts, keep using `source ./init.sh` and `source ./uninit.sh`. Every command described below also works via `make` so automations and editors like Cursor can run the same flows non-interactively.

## 1. Prerequisites

| Requirement | Notes |
| --- | --- |
| Python 3.10+ | macOS ships with an older Python; install via [Homebrew](https://brew.sh) or `pyenv`. |
| Git | Required for version control. `xcode-select --install` on macOS installs Git. |
| Homebrew (macOS) / apt (Debian/Ubuntu) | Needed for system packages. |
| Optional: [Cursor](https://cursor.sh), OpenAI Codex, Claude Code | Works great alongside this repository. |

## 2. Start-of-Day Setup

1. Open a shell in the project root (`prt`).
2. Choose one of the following:
   * `source ./init.sh` – Sets up/activates the `prt_env` virtual environment in your current shell.
   * `make init` – Runs the same logic in a single shell process (handy for automation).
3. When the environment finishes:
   * `(prt_env)` prefix should be in your prompt.
   * Pre-commit hooks are installed.
   * Dependencies from `requirements.txt` are available.

If you see activation issues, run `source prt_env/bin/activate` manually. The init scripts verify installation by importing `textual`, `sqlalchemy`, and `typer`.

## 3. End-of-Day Cleanup

* `source ./uninit.sh` – Deactivates the environment in your current shell and clears old SQLCipher variables.
* `make uninit` – Same clean-up flow, executed through Make.

If your shell still shows `(prt_env)`, run `deactivate` manually.

## 4. Daily Command Cheat Sheet

| Intent | Command |
| --- | --- |
| Launch TUI | `make tui` or `python -m prt_src` |
| Run classic CLI | `make run-classic` or `python -m prt_src --classic` |
| Debug TUI with fixtures | `make run-debug` or `python -m prt_src --debug` |
| Quick tests | `make test` (runs `pytest -x`) |
| Full tests | `make all-tests` (runs `pytest -v`) |
| Coverage report | `make coverage` |
| Lint | `make lint` (`ruff check`) |
| Auto-fix formatting | `make format` (`ruff --fix` + `black`) |
| All quality checks | `make check` (lint + tests) |
| Clean caches/builds | `make clean` |
| Check outdated packages | `make deps-check` |
| Run pre-commit everywhere | `make pre-commit-all` |

> **Cursor/LLM tip:** Paste the table above into your prompt or keep it pinned in a scratchpad so Codex/Claude can cite the correct commands for you.

## 5. Recommended Workflow with AI Helpers

1. **Frame the task** – Describe the goal, related modules (e.g., `prt_src/contacts`), and reference docs to your AI helper.
2. **Retrieve context quickly** – Use `make help`, skim `docs/DEV_SETUP.md`, and consult the doc map in the README (below).
3. **Let the AI draft changes** – Provide file paths and expectations; ask for focused diffs.
4. **Run targeted checks** – Use `make lint` / `make test` locally. For UI work, run `make tui` to verify behavior.
5. **Iterate** – Commit early with small chunks; ask AI to adjust failing tests or refine docs.
6. **Before submitting** – Ensure a clean `git status`, run `make check`, and summarize changes in the PR template.

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
3. Re-run `source ./init.sh` (or `make init`)
4. If pip installs fail, confirm Homebrew/apt availability and rerun.

For persistent issues, check `requirements.txt` for pinned versions and install manually inside the venv.

## 8. Documentation Map & Freshness

Use this section to jump to deeper context quickly. `✅` marks docs kept up to date; `🕰️` indicates historical notes that may be stale.

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

## 9. Backlog & Optional Improvements (from Issue #101)

* 🟨 Add `.vscode/settings.json` with recommended formatters + type checking.
* 🟨 Configure a GitHub Actions workflow running `pytest` + `ruff`.
* 🟨 Enable Dependabot for pip dependencies (needs repo admin).

When you’re ready, spin each bullet into its own task so AI helpers can drive implementation while you review.

## 10. Handy Snippets

```bash
# Run lint + tests in one go
make check

# Snapshot database status from the CLI
python -m prt_src db-status

# Import Google Takeout export interactively - many things are not in the TUI yet
python -m prt_src --classic
```

If you find yourself repeating a command three times, consider adding a Make target or shell alias and document it here.

## 11. TUI Debugging System

### **Automated Textual Debug Workflow**

WORK IN PROGRESS - WORTH A TRY

For TUI development and debugging, use the comprehensive debug system in `docs/TUI/DEBUGGING/`:

```bash
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
- **Screenpipe Integration**: Visual state capture correlated with app state

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


