# 🛠️ Developer Setup Guide

## 🚀 Quick Start (30 seconds)

```bash
git clone https://github.com/richbodo/prt.git
cd prt
source ./init.sh    # Installs everything automatically
python -m prt_src   # Launch TUI immediately
```

**That's it!** You now have a fully working PRT development environment.

## 📋 What init.sh Does

The setup script automatically:

1. **🐍 Creates Python virtual environment** (`prt_env/`)
2. **📦 Installs all dependencies** (runtime + development)
3. **🔧 Sets up pre-commit hooks** (ruff + black)
4. **✅ Verifies installation** (imports test)
5. **📖 Shows quick start guide**

## 🎯 Development Workflow

### Daily Development
```bash
# Activate environment (if not already active)
source prt_env/bin/activate

# Run the TUI
python -m prt_src

# Run classic CLI  
python -m prt_src --classic

# Run with debug data
python -m prt_src --debug
```

### Testing
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_tui_app.py -v

# Run with coverage
python -m pytest tests/ --cov=prt_src --cov-report=html
```

### Code Quality Tools

PRT uses automated code formatting and linting:

```bash
# Manually run code quality checks
pre-commit run --all-files

# Install pre-commit hooks (done automatically by init.sh)
pre-commit install
```

**Tools used:**
- **ruff**: Fast Python linter (replaces flake8)
- **black**: Code formatter  
- **pre-commit**: Runs tools automatically on git commit

**Configuration:**
- **`pyproject.toml`**: Tool settings (line length 100, ruff rules, etc.)
- **`.pre-commit-config.yaml`**: Defines when tools run and versions
- **Automatic formatting**: Ruff fixes issues, Black formats code on every commit

### 🚀 Pull Request Workflow

**We encourage PRs for all changes** - they trigger automated code reviews:

```bash
# Create feature branch
git checkout -b feature/your-improvement

# Make changes, commit with good messages
git commit -m "feat: add awesome feature"

# Push and create PR
git push -u origin feature/your-improvement
gh pr create --title "Add awesome feature" --body "Description..."
```

**PR Benefits:**
- ✅ **Automated code review** (Claude + GitHub Actions)  
- ✅ **CI/CD testing** runs full test suite
- ✅ **Code quality checks** (ruff, black, tests)
- ✅ **Documentation review** ensures clarity
- ✅ **Architecture discussion** in PR comments

## 🏗️ Project Architecture

### Directory Structure
```
prt/
├── prt_src/           # Main application code
│   ├── tui/          # Textual UI framework
│   │   ├── screens/  # All 16 TUI screens
│   │   ├── widgets/  # Custom UI components
│   │   └── services/ # UI data services
│   ├── core/         # Business logic layer
│   │   ├── components/ # Reusable components
│   │   └── search_*/ # Search infrastructure
│   └── models.py     # SQLAlchemy data models
├── docs/             # Documentation
├── tests/            # Test suite (pytest)
├── migrations/       # Database migrations
└── prt_data/         # User data directory
```

### Key Technologies
- **UI**: Textual (modern TUI framework)
- **Database**: SQLite with FTS5 search
- **ORM**: SQLAlchemy
- **CLI**: Typer
- **Testing**: pytest
- **Code Quality**: ruff + black

## 🔧 Environment Setup

### Requirements Files
- **`requirements.txt`**: Core runtime dependencies
- **`requirements-dev.txt`**: Development tools only

### Virtual Environment
```bash
# Manual venv setup (if init.sh fails)
python -m venv prt_env
source prt_env/bin/activate  # Linux/Mac
prt_env\Scripts\activate     # Windows

pip install -r requirements.txt -r requirements-dev.txt
```

### Database Setup
```bash
# Database is auto-created on first run
python -m prt_src setup  # Manual setup if needed

# Check database status
python -m prt_src db-status
```

## 🧪 Testing Strategy

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: TUI screen interactions
- **Performance Tests**: 5000+ contact handling
- **API Tests**: PRTAPI functionality

### Running Tests
```bash
# Quick test run
python -m pytest tests/ -x

# Full test suite with coverage
python -m pytest tests/ --cov=prt_src --cov-report=html --cov-report=term

# Test specific functionality
python -m pytest tests/test_tui_* -v    # TUI tests
python -m pytest tests/test_core_* -v   # Core logic tests
```

## 🚨 Troubleshooting

### Common Issues

**❌ "textual not found"**
```bash
# Reinstall dependencies
source ./init.sh
```

**❌ "Database locked"**
```bash
# Check for running PRT instances
ps aux | grep prt_src
kill <process_id>  # If needed
```

**❌ "Import errors"**
```bash
# Verify virtual environment
which python  # Should show prt_env path
pip list | grep textual  # Should show textual>=0.47.0
```

**❌ "Pre-commit failing"**
```bash
# Update pre-commit
pre-commit autoupdate
pre-commit run --all-files
```

### Getting Help

1. **Check existing issues**: https://github.com/richbodo/prt/issues
2. **Read docs**: All documentation in `/docs/`
3. **Create issue**: Detailed bug reports welcome
4. **Join discussions**: GitHub Discussions for questions

## 📝 Contributing

### Code Style
- **Line length**: 100 characters
- **Imports**: isort with black profile
- **Linting**: ruff with E, F, I rules
- **Format**: black (runs automatically)

### Commit Messages
```bash
feat: add new awesome feature
fix: resolve critical bug
docs: update setup instructions
test: add missing unit tests
refactor: improve code structure
```

### Documentation
- Update relevant docs with code changes
- Add docstrings to new functions/classes
- Update CLI help text if commands change
- Keep README.md current

---

**Welcome to PRT development! 🎉**

This setup should give you everything needed to contribute to PRT. The modern TUI interface makes contact management powerful and intuitive - we're excited to see what you build!
