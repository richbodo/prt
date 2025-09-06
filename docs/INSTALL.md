# 🚀 PRT Installation Guide

**QUICK SETUP**: Most users should use the [Quick Start](#quick-start) method below.

For detailed developer setup, see [docs/DEV_SETUP.md](DEV_SETUP.md).

## 🚀 Quick Start (Recommended)

**One command setup for all platforms:**

```bash
git clone https://github.com/richbodo/prt.git
cd prt
source ./init.sh    # Installs everything automatically
python -m prt_src   # Launch modern TUI interface
```

**That's it!** The `init.sh` script handles all dependencies automatically.

## 📋 What Gets Installed

- **Python virtual environment** (`prt_env/`)
- **Core runtime dependencies** (textual, sqlalchemy, typer, etc.)
- **Development tools** (pytest, ruff, black, pre-commit)
- **AI/LLM tools** (langchain, transformers - optional)
- **Pre-commit hooks** for code quality

## 🖥️ Platform Support

| Platform | Status | Notes |
|----------|--------|--------|
| **macOS** | ✅ Fully Supported | Requires Homebrew |
| **Linux** | ✅ Fully Supported | Debian/Ubuntu tested |
| **Windows** | ⚠️ Not Tested | Should work with WSL |

## 📦 System Requirements

- **Python 3.8+** 
- **Git** 
- **macOS**: Homebrew package manager
- **Linux**: Standard build tools (`build-essential` on Ubuntu)

## 🔧 Manual Installation (Advanced)

If the automatic setup fails, you can install manually:

```bash
# Clone repository
git clone https://github.com/richbodo/prt.git
cd prt

# Create virtual environment
python3 -m venv prt_env
source prt_env/bin/activate  # Linux/Mac
# prt_env\Scripts\activate   # Windows (untested)

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Set up development tools
pre-commit install

# Verify installation
python -c "import textual; import sqlalchemy; print('✅ Installation successful')"
```

## 🧪 Verification

After installation, verify everything works:

```bash
# Test modern TUI interface
python -m prt_src

# Test classic CLI
python -m prt_src --classic --help

# Run test suite
python -m pytest tests/ -v

# Check database status
python -m prt_src db-status
```

## 🚨 Troubleshooting

### Common Issues

**❌ "textual not found"**
- Run: `source ./init.sh` (reinstalls everything)

**❌ "python command not found"**
- Install Python 3.8+ from python.org
- On Ubuntu: `sudo apt install python3 python3-venv`

**❌ "Virtual environment activation fails"**
- Check you're in the `prt/` directory
- Run: `source prt_env/bin/activate` manually

**❌ "Homebrew required" (macOS)**
- Install: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

**❌ "Build tools missing" (Linux)**
- Ubuntu: `sudo apt install build-essential python3-dev`
- CentOS: `sudo yum groupinstall "Development Tools"`

### Getting Help

1. **Check logs**: Installation errors are printed to terminal
2. **GitHub Issues**: https://github.com/richbodo/prt/issues
3. **Documentation**: All docs in `/docs/` directory
4. **Clean install**: `rm -rf prt_env && source ./init.sh`

## 📚 Next Steps

Once installed:

1. **📖 Read**: [DEV_SETUP.md](DEV_SETUP.md) for development workflow
2. **🎮 Explore**: Launch `python -m prt_src` to explore the TUI
3. **🧪 Test**: Run `python -m pytest tests/` to verify everything works
4. **🚀 Contribute**: Create PRs for improvements!

---

**Welcome to PRT! 🎉** 

PRT provides both a modern Textual TUI and classic CLI for managing personal relationship data with enterprise-grade features.
