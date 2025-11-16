# Personal Relationship Toolkit (PRT)

Privacy-first contact management with AI-powered search

A privacy-first contact management system with AI-powered search.
All data stored locally on your machine, no cloud sync.

**Default behavior**: Launches TUI (Text User Interface)
**First time?** Run with `--setup` to import contacts or `--debug` to try sample data.

## Options

- `--debug, -d` - Run with sample data (safe, isolated database)
- `--regenerate-fixtures` - Reset sample data (use with --debug)
- `--setup` - First-time setup: import contacts or try demo data
- `--cli` - Use command-line interface instead of TUI
- `--classic` - Force classic CLI mode (disable TUI attempt)
- `--tui` - Use TUI interface (default)
- `--prt-debug-info` - Display system diagnostic information and exit
- `--model, -m MODEL` - Choose AI model (e.g. 'gpt-oss-20b', 'mistral-7b-instruct')
  Use 'list-models' to see options. Put this flag BEFORE --chat.
- `--chat [TEXT]` - Start AI chat mode. Provide query text or use --chat=""
  for interactive mode. Use AFTER --model flag.
- `--help` - Show this message and exit.

## Commands

- `test-db` - Test database connection and credentials.
- `list-models` - List available LLM models with support status and hardware requirements.
- `prt-debug-info` - Display comprehensive system diagnostic information and exit.
- `db-status` - Check the database status.

## Getting Started

```bash
python -m prt_src --setup         # First-time setup with your data
python -m prt_src --debug         # Try with sample data (safe)
python -m prt_src                 # Launch main interface (TUI)
```

## Chat with AI

```bash
python -m prt_src --model gpt-oss-20b --chat
python -m prt_src --model mistral-7b-instruct --chat "find friends"
python -m prt_src --chat="" --model gpt-oss-20b
```

**IMPORTANT**: Put --model flag BEFORE --chat to avoid parsing issues

## More Help

```bash
python -m prt_src list-models     # Show available AI models
```

Documentation: https://github.com/richbodo/prt