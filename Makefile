# PRT Development Makefile
# Provides convenient shortcuts for common development tasks

SHELL := /bin/bash
.ONESHELL:

.SILENT: init uninit

.PHONY: help init uninit install clean test tests lint format run run-classic run-debug tui check deps-check all-tests coverage pre-commit-all

# Default target
help:
	@echo "🛠️  PRT Development Commands"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make init        Full environment setup (like \"source ./init.sh\")"
	@echo "  make uninit      Deactivate environment (like \"source ./uninit.sh\")"
	@echo "  make tui         Launch PRT TUI"
	@echo "  make test        Run test suite"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make lint        Run code linting (ruff)"
	@echo "  make format      Format code (black + ruff --fix)"
	@echo "  make check       Run all quality checks (lint + test + coverage)"
	@echo "  make clean       Clean build artifacts and cache"
	@echo ""  
	@echo "🎮 Run Modes:"
	@echo "  make tui         Modern TUI interface"
	@echo "  make run-classic Classic CLI interface"
	@echo "  make run-debug   TUI with debug/fixture data"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test        Quick test run"
	@echo "  make all-tests   Full test suite with verbose output"
	@echo "  make coverage    Generate test coverage report"
	@echo ""
	@echo "⚙️  Maintenance:"
	@echo "  make deps-check  Check for dependency updates"
	@echo "  make pre-commit-all  Run pre-commit on all files"

# Development setup
init:
	set -euo pipefail
	
	UNAME_OUT="$(uname -s)"
	echo "Os is: "
	echo "${UNAME_OUT}"
	
	case "${UNAME_OUT}" in
		Darwin*) OS="mac" ;;
		Linux*) OS="linux" ;;
		*) echo "Unsupported operating system: ${UNAME_OUT}"; exit 1 ;;
	esac
	
	if [[ "${OS}" == "mac" ]]; then
		echo "Os is: "
		echo "${OS}"
		echo "Checking for Homebrew..."
		if ! command -v brew >/dev/null; then
			echo "Error: Homebrew is required but not installed. Please install Homebrew first."
			echo "Visit https://brew.sh for installation instructions."
			exit 1
		fi
		echo "Homebrew found at: $(which brew)"
		echo "SQLCipher dependencies removed - using regular SQLite now"
	elif [[ "${OS}" == "linux" ]]; then
		if command -v apt-get >/dev/null; then
			echo "Installing system dependencies via apt..."
			if [[ "${EUID}" -ne 0 ]] && command -v sudo >/dev/null; then
				sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-dev build-essential pkg-config || { echo "Failed to install system packages"; exit 1; }
			else
				apt-get update && apt-get install -y python3 python3-venv python3-dev build-essential pkg-config || { echo "Failed to install system packages"; exit 1; }
			fi
		else
			echo "Error: apt-get not found. Please install required dependencies manually."
			exit 1
		fi
	fi
	
	if [[ ! -d "prt_env" ]]; then
		echo "Creating new virtual environment: prt_env"
		python3 -m venv prt_env || { echo "Failed to create virtual environment"; exit 1; }
	
		source prt_env/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }
		if [[ "${VIRTUAL_ENV}" != "$(pwd)/prt_env" ]]; then
			echo "Error: Virtual environment not properly activated"
			exit 1
		fi
		pip install --upgrade pip
		echo "📦 Installing all dependencies (runtime + development)..."
		pip install -v -r requirements.txt || { echo "Failed to install requirements"; exit 1; }
		echo "✅ All packages installed successfully"
	else
		source prt_env/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }
	fi
	
	if [[ -n "${VIRTUAL_ENV:-}" ]]; then
		echo "Virtual environment activated! You should see (prt_env) in your prompt."
		echo "If you don't see (prt_env), try running: source prt_env/bin/activate"
	
		pre-commit install || { echo "Failed to install pre-commit hooks"; exit 1; }
		echo "🔧 Pre-commit hooks installed"
	
		if [[ "${RUN_PRE_COMMIT:-0}" == "1" ]]; then
			pre-commit run --all-files || { echo "pre-commit run failed"; exit 1; }
		fi
	
		echo "🧪 Verifying installation..."
		python -c "import textual; import sqlalchemy; import typer; print('✅ Core packages verified')" || { echo "❌ Installation verification failed"; exit 1; }
	
		echo ""
		echo "🎉 PRT development environment ready!"
		echo ""
		echo "🚀 Quick Start:"
		echo "  python -m prt_src        # Launch modern TUI"
		echo "  python -m prt_src --classic  # Classic CLI"
		echo "  python -m pytest tests/  # Run tests"
		echo "  make help                # See all make commands"
		echo ""
		echo "📚 More info: https://github.com/richbodo/prt"
	else
		echo "Warning: Virtual environment not properly activated"
	fi
	
install: init
	@echo ""
	@echo "✅ Development environment ready via 'make init'"

uninit:
	set -euo pipefail
	
	if [[ -n "${VIRTUAL_ENV:-}" ]]; then
		echo "Deactivating virtual environment..."
		if declare -F deactivate >/dev/null; then
			deactivate
		elif [[ -f "${VIRTUAL_ENV}/bin/activate" ]]; then
			source "${VIRTUAL_ENV}/bin/activate"
			deactivate
		else
			echo "Could not locate deactivate function; please run 'deactivate' manually if your shell remains activated."
		fi
		echo "Virtual environment deactivated!"
	else
		echo "No active virtual environment detected."
	fi
	
	if [[ -n "${SQLCIPHER_PATH:-}" ]]; then
		echo "Cleaning up SQLCipher environment variables..."
		unset SQLCIPHER_PATH
		unset LDFLAGS
		unset CPPFLAGS
		echo "SQLCipher environment variables cleaned up!"
	fi
	
# Run targets
run: tui

run-classic:
	@echo "🖥️  Launching PRT Classic CLI..."
	@bash -c "source prt_env/bin/activate && python -m prt_src --classic"

run-debug:
	@echo "🐛 Launching PRT TUI with debug data..."
	@bash -c "source prt_env/bin/activate && python -m prt_src --debug"

tui:
	@echo "🚀 Launching PRT TUI..."
	@bash -c "source prt_env/bin/activate && python -m prt_src"

# Code quality
lint:
	@echo "🔍 Running code linting..."
	@bash -c "source prt_env/bin/activate && ruff check prt_src/ tests/"

format:
	@echo "✨ Formatting code..."
	@bash -c "source prt_env/bin/activate && ruff check --fix prt_src/ tests/"
	@bash -c "source prt_env/bin/activate && black prt_src/ tests/"
	@echo "✅ Code formatted"

# Testing
test:
	@echo "🧪 Running test suite..."
	@bash -c "source prt_env/bin/activate && python -m pytest tests/ -x"

all-tests:
	@echo "🧪 Running full test suite..."
	@bash -c "source prt_env/bin/activate && python -m pytest tests/ -v"

tests: test

coverage:
	@echo "📊 Generating test coverage report..."
	@bash -c "source prt_env/bin/activate && python -m pytest tests/ --cov=prt_src --cov-report=html --cov-report=term"
	@echo "📊 Coverage report generated in htmlcov/"

# Comprehensive check
check: lint test
	@echo "✅ All quality checks passed!"

# Maintenance  
clean:
	@echo "🧹 Cleaning build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.coverage" -delete 2>/dev/null || true
	@rm -rf htmlcov/ .coverage .pytest_cache/ build/ dist/ *.egg-info/ 2>/dev/null || true
	@echo "✅ Cleaned up"

deps-check:
	@echo "🔍 Checking for dependency updates..."
	@bash -c "source prt_env/bin/activate && pip list --outdated"

pre-commit-all:
	@echo "🔧 Running pre-commit on all files..."
	@bash -c "source prt_env/bin/activate && pre-commit run --all-files"

# Database shortcuts
db-status:
	@echo "📊 Checking database status..."
	@bash -c "source prt_env/bin/activate && python -m prt_src db-status"

db-backup:
	@echo "💾 Creating database backup..."
	@bash -c "source prt_env/bin/activate && python -m prt_src backup"

# Alias for convenience
cli: run-classic
debug: run-debug
