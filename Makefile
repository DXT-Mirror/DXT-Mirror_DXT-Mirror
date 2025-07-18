# DXT Curator Makefile
# Common development and maintenance tasks

.PHONY: help install dev test clean lint format security check-deps run-example

help:
	@echo "DXT Curator - Available commands:"
	@echo ""
	@echo "🚀 Setup & Installation:"
	@echo "  make install     - Install package in production mode"
	@echo "  make dev         - Install package in development mode"
	@echo "  make setup       - Complete development setup"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linting checks"
	@echo "  make format      - Format code"
	@echo "  make security    - Run security checks"
	@echo "  make check-deps  - Check for dependency vulnerabilities"
	@echo ""
	@echo "🔧 Development:"
	@echo "  make clean       - Clean build artifacts"
	@echo "  make build       - Build package"
	@echo "  make run-example - Run example workflow"
	@echo ""
	@echo "📊 Operations:"
	@echo "  make discover    - Discover 10 repositories"
	@echo "  make status      - Show inventory status"
	@echo "  make ready       - Show repositories ready to mirror"

install:
	pip install .

dev:
	pip install -e ".[dev]"

setup:
	python setup_dev.py

test:
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v --cov=dxt_curator --cov-report=html --cov-report=term-missing

lint:
	@echo "🔍 Running linting checks..."
	python -m flake8 dxt_curator/
	python -m pylint dxt_curator/
	python -m mypy dxt_curator/

format:
	@echo "🎨 Formatting code..."
	python -m black dxt_curator/
	python -m isort dxt_curator/

security:
	@echo "🔒 Running security checks..."
	python -m bandit -r dxt_curator/
	python -m safety check

check-deps:
	@echo "📦 Checking dependencies..."
	pip list --outdated
	python -m pip-audit

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	@echo "🔨 Building package..."
	python -m build

run-example:
	@echo "🚀 Running example workflow..."
	@echo "This will discover 5 repositories as a demo"
	@if [ ! -f .env ]; then echo "⚠️  No .env file found. Copy .env.example to .env and add your API keys"; exit 1; fi
	python -c "from dxt_curator import SimpleDXTWorkflow; w = SimpleDXTWorkflow(); w.discover_and_evaluate(5)"

discover:
	@echo "🔍 Discovering repositories..."
	dxt-curator discover 10

status:
	@echo "📊 Inventory status..."
	dxt-curator status

ready:
	@echo "✅ Repositories ready to mirror..."
	dxt-curator ready

# Advanced operations
recheck:
	@echo "🔄 Rechecking repositories..."
	dxt-curator recheck

search:
	@echo "🔍 Searching inventory..."
	@read -p "Enter search term: " term; dxt-curator search "$$term"

export:
	@echo "📤 Exporting inventory..."
	dxt-curator export --output inventory_export.json
	@echo "📁 Exported to inventory_export.json"

# Development helpers
deps-update:
	@echo "📦 Updating dependencies..."
	pip install --upgrade pip
	pip install --upgrade -e ".[dev]"

check-syntax:
	@echo "🔍 Checking syntax..."
	python -m py_compile dxt_curator/core/*.py
	python -m py_compile dxt_curator/utils/*.py
	python -m py_compile dxt_curator/cli/*.py

validate-config:
	@echo "⚙️  Validating configuration..."
	python -c "from dxt_curator.utils.config import Config; c = Config(); print('✅ Configuration valid')"

# Documentation
docs:
	@echo "📚 Documentation files:"
	@echo "  README.md - Main documentation"
	@echo "  EXAMPLES.md - Usage examples"
	@echo "  LICENSE - Apache 2.0 license"
	@echo "  pyproject.toml - Package configuration"

# Quick health check
health:
	@echo "🏥 Health check..."
	@echo "Python version: $(shell python --version)"
	@echo "Package installed: $(shell pip show dxt-curator | grep Version || echo 'Not installed')"
	@echo "Config file: $(shell [ -f dxt_curator_config.json ] && echo 'Found' || echo 'Not found (optional)')"
	@echo "Environment: $(shell [ -f .env ] && echo 'Found' || echo 'Not found - copy .env.example')"