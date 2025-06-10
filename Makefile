.PHONY: test test-cache test-regression test-integration install-dev clean lint format

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Run all tests
test:
	pytest tests/ -v

# Run cache-specific tests (addresses LLM-identified issue)
test-cache:
	pytest tests/ -v -m "cache" --tb=long

# Run regression tests for the cache fix
test-regression:
	pytest tests/ -v -m "regression" --tb=long

# Run integration tests
test-integration:
	pytest tests/ -v -m "integration" --tb=short

# Run LLM-identified issue tests specifically
test-llm-issues:
	pytest tests/test_llm_identified_issues.py -v --tb=long

# Run tests with coverage
test-coverage:
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

# Run JavaScript tests
test-js:
	npm test

# Build JavaScript
build-js:
	npm run build

# Run all tests (Python + JavaScript)
test-all: test test-js

# Install and run quick validation
validate: install-dev test-quick test-cache-behavior
	@echo "✅ Quick validation completed successfully"

# Full CI-like test suite
test-ci: install-dev test-coverage test-regression test-integration lint
	@echo "✅ Full CI test suite completed"