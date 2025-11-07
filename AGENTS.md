# Repository Guidelines

## Project Structure & References
`prt_src/` houses runtime code (`core/` logic, `tui/` widgets, `llm_*` orchestration). Tests mirror that layout across `tests/unit`, `tests/integration`, `tests/e2e`, and `tests/llm_contracts`, using fixtures in `tests/fixtures.py`. Docs live in `docs/` (`DEV_SETUP.md`, `TESTING_STRATEGY.md`, `TUI/*` specs) and offline manuals belong in `EXTERNAL_DOCS/` via `./download_library_src.sh`. Local directories (`prt_env/`, `prt_data/`, `exports/`, `directories/`) contain envs, databases, and exports—never commit them.

## Build & Development Loop
Run `source ./init.sh` to activate the venv (pre-commit included) and `source ./uninit.sh` to clean up. Use `python -m prt_src` (add `--debug` when fixtures help) for the Textual UI and `python -m prt_src.cli` for scripted flows. Keep to the `docs/DEV_SETUP.md` loop: `./prt_env/bin/pytest -m "unit or integration"`, `./prt_env/bin/ruff check --fix prt_src/ tests/ && ./prt_env/bin/black prt_src/ tests/`, and `python -m prt_src.cli setup` / `db-status` whenever migrations move.

## Coding & TUI Conventions
Stick to Python ≥3.8, 4-space indents, snake_case functions, PascalCase widgets, and UPPER_SNAKE_CASE constants; keep prompts, SQL, and schema helpers near their consumers. `docs/TUI/TUI_Style_Guide.md` governs UX: reserved keys (`esc`, `n`, `x`, `?`, `h`, `b`) stay immutable, TextAreas use `Ctrl+J` (surface the hint), and text widgets should inherit from `Static`/`ModeAwareWidget`. Favor minimal containers and lean on logging (`tail -f prt_data/prt.log`) while debugging.

## Testing & QA Expectations
The pyramid in `docs/TESTING_STRATEGY.md` still rules: `./prt_env/bin/pytest -m unit` (<1 s) for deterministic helpers, `./prt_env/bin/pytest -m integration` (<5 s) for DB/TUI workflows with MockLLMService, and `npx promptfoo eval -c tests/llm_contracts/promptfoo.yaml` whenever prompts or tool schemas change. Reserve `pytest -m "slow and requires_llm"` for releases, log visual/perf checks in `docs/MANUAL_TESTING.md`, and keep snapshot/Pilot tests beside their screens—always `await pilot.pause()` before asserting UI state.

## LLM Configuration & Safety
All settings live in `prt_data/prt_config.json` (see `docs/examples/prt_config_llm_settings.json`): adjust models/timeouts under `llm`, guard writes with `llm_permissions`, swap prompts via `llm_prompts`, and toggle logging or experiments through `llm_developer`. Tool flows should match `docs/LLM_Integration/README.md` and `docs/LLM_TOOL_CHAINING_EXAMPLES.md` (e.g., `save_contacts_with_images` → `generate_directory`). Every write path snapshots the database per `docs/BACKUP_SYSTEM.md`, so keep `prt_data/backups/` intact and mention `backup_id`s when relevant.

## Commit & Pull Request Guidelines
Branch off `main` with names like `feature/contact-search-cards` or `fix/backup-race`, and keep commits concise Title Case (issue tags optional). Before opening a PR, run Ruff, Black, `pytest -m "unit or integration"`, and any contract/manual tests you touched; list those commands plus screenshots for UI work in the description. Link the roadmap item or spec you updated so reviewers can trace intent, and edit the relevant doc whenever commands, flows, or safeguards change.
