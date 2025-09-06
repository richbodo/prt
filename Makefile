# PRT Development Makefile
# Provides convenient shortcuts for common development tasks

.PHONY: help install clean test lint format run run-classic run-debug check deps-check all-tests coverage pre-commit-all

# Default target
help:
	@echo "🛠️  PRT Development Commands"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make install     Install all dependencies (like source ./init.sh)"
	@echo "  make run         Launch PRT TUI"  
	@echo "  make test        Run test suite"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make lint        Run code linting (ruff)"
	@echo "  make format      Format code (black + ruff --fix)"
	@echo "  make check       Run all quality checks (lint + test + coverage)"
	@echo "  make clean       Clean build artifacts and cache"
	@echo ""  
	@echo "🎮 Run Modes:"
	@echo "  make run         Modern TUI interface (default)"
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
install:
	@echo "📦 Setting up PRT development environment..."
	@if [ ! -d "prt_env" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv prt_env; \
	fi
	@echo "Activating virtual environment and installing dependencies..."
	@bash -c "source prt_env/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
	@bash -c "source prt_env/bin/activate && pre-commit install"
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "🚀 Quick start: make run"

# Run targets
run:
	@echo "🚀 Launching PRT TUI..."
	@bash -c "source prt_env/bin/activate && python -m prt_src"

run-classic:
	@echo "🖥️  Launching PRT Classic CLI..."
	@bash -c "source prt_env/bin/activate && python -m prt_src --classic"

run-debug:
	@echo "🐛 Launching PRT TUI with debug data..."
	@bash -c "source prt_env/bin/activate && python -m prt_src --debug"

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
tui: run
cli: run-classic
debug: run-debug
