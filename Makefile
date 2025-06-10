.PHONY: help test-python test-js test-all test-cache test-regression test-integration install-dev clean lint format

# Default target
help:
	@echo "📋 Marimo-OpenSCAD Test Commands"
	@echo ""
	@echo "🔴 PYTHON BACKEND TESTS:"
	@echo "  make test-python           - Run all Python tests"
	@echo "  make test-cache            - 🔥 CRITICAL: Cache behavior tests"
	@echo "  make test-regression       - 🎯 LLM regression tests"
	@echo "  make test-llm-issues       - 🚨 Specific LLM-identified issues"
	@echo "  make test-integration      - 🔗 Integration tests"
	@echo "  make test-coverage         - 📊 Python tests with coverage"
	@echo ""
	@echo "🟨 JAVASCRIPT FRONTEND TESTS:"
	@echo "  make test-js               - Run JavaScript widget tests"
	@echo "  make build-js              - Build JavaScript widget"
	@echo ""
	@echo "🔄 COMBINED TESTS:"
	@echo "  make test-all              - Run both Python + JavaScript tests"
	@echo "  make validate              - Quick validation (fast subset)"
	@echo "  make test-ci               - Full CI-like test suite"
	@echo ""
	@echo "🔧 DEVELOPMENT:"
	@echo "  make install-dev           - Install development dependencies"
	@echo "  make format                - Format code (black, isort)"
	@echo "  make lint                  - Lint code (flake8, mypy)"
	@echo "  make clean                 - Clean build artifacts"

# Install development dependencies
install-dev:
	@echo "📦 Installing Python development dependencies..."
	pip install -e ".[dev]"
	@echo "📦 Installing JavaScript dependencies..."
	npm install

# === PYTHON BACKEND TESTS ===

# Run all Python tests
test-python:
	@echo "🐍 Running all Python backend tests..."
	pytest tests/ -v

# 🔥 CRITICAL: Run cache-specific tests (addresses LLM-identified issue)
test-cache:
	@echo "🔥 CRITICAL: Running cache behavior tests (LLM regression prevention)..."
	pytest tests/ -v -m "cache" --tb=long

# 🎯 Run regression tests for the cache fix
test-regression:
	@echo "🎯 Running LLM regression tests..."
	pytest tests/ -v -m "regression" --tb=long

# 🔗 Run integration tests
test-integration:
	@echo "🔗 Running integration tests..."
	pytest tests/ -v -m "integration" --tb=short

# 🚨 Run LLM-identified issue tests specifically
test-llm-issues:
	@echo "🚨 Running specific LLM-identified issue tests..."
	pytest tests/test_llm_identified_issues.py -v --tb=long

# 📊 Run tests with coverage
test-coverage:
	@echo "📊 Running Python tests with coverage..."
	pytest tests/ --cov=marimo_openscad --cov-report=html --cov-report=term-missing

# Run cache behavior tests (critical for preventing regression)
test-cache-behavior:
	pytest tests/test_cache_behavior.py -v --tb=long

# Run viewer integration tests
test-viewer:
	pytest tests/test_viewer_integration.py -v --tb=short

# Quick test for CI (fast subset)
test-quick:
	pytest tests/ -v -m "not slow" --tb=short

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Lint code
lint:
	flake8 src/ tests/
	mypy src/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build package
build:
	python -m build

# === JAVASCRIPT FRONTEND TESTS ===

# 🟨 Run JavaScript tests
test-js:
	@echo "🟨 Running JavaScript widget tests..."
	npm test

# 🔧 Build JavaScript
build-js:
	@echo "🔧 Building JavaScript widget..."
	npm run build

# === COMBINED TESTS ===

# 🔄 Run all tests (Python + JavaScript)
test-all: test-python test-js
	@echo "✅ All tests completed (Python + JavaScript)"

# ⚡ Install and run quick validation
validate: install-dev test-quick test-cache
	@echo "✅ Quick validation completed successfully"

# 🚀 Full CI-like test suite
test-ci: install-dev test-coverage test-regression test-integration lint build-js
	@echo "✅ Full CI test suite completed (Python + JavaScript)"