# 🐍 PlomTTS Client PyPI Deployment Makefile
# Makefile for building and deploying plomtts-client to PyPI

.PHONY: help clean build test test-live check upload upload-test install-dev lint format

# Default target
help:
	@echo "📦 PlomTTS Client PyPI Deployment"
	@echo ""
	@echo "Available targets:"
	@echo "  🧹 clean         - Remove build artifacts and cache files"
	@echo "  🏗️  build        - Build distribution packages"
	@echo "  🧪 test          - Run tests (excludes live tests)"
	@echo "  🌐 test-live     - Run live integration tests"
	@echo "  ✅ check         - Check package integrity"
	@echo "  🤖 deploy-info   - Show information about automated deployment"
	@echo "  🛠️  install-dev  - Install in development mode"
	@echo "  🎨 lint          - Run linting checks"
	@echo "  ✨ format        - Format code with black and isort"
	@echo "  🔄 all           - Clean, build, test, and check (no upload - automated via GitHub)"

# Variables
PYTHON := python3
PIP := pip3
TWINE := twine

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Clean complete"

# Install development dependencies
install-dev:
	@echo "🛠️ Installing development dependencies..."
	"${PIP}" install -e .[dev]
	"${PIP}" install build twine
	@echo "✅ Development environment ready"

# Format code
format:
	@echo "✨ Formatting code..."
	black .
	isort .
	@echo "✅ Code formatted"

# Run linting
lint:
	@echo "🎨 Running linting checks..."
	black --check .
	isort --check-only .
	@echo "✅ Linting complete"

# Run tests (excluding live tests)
test:
	@echo "🧪 Running tests (excluding live tests)..."
	pytest tests/ --verbose -m "not live"
	@echo "✅ Tests complete"

# Run live integration tests
test-live:
	@echo "🌐 Running live integration tests..."
	pytest tests/ --verbose -m live
	@echo "✅ Live tests complete"

# Build distribution packages
build: clean
	@echo "🏗️ Building distribution packages..."
	"${PYTHON}" -m build
	@echo "✅ Build complete"

# Check package integrity
check: build
	@echo "✅ Checking package integrity..."
	"${TWINE}" check dist/*
	@echo "✅ Package check complete"

# Complete workflow for testing
all: clean install-dev format lint test check
	@echo "🚀 Ready for deployment! Push to main branch to auto-deploy to PyPI."

# Version bump helpers
bump-patch:
	@echo "🔢 Bumping patch version..."
	@current_version="$$(grep 'version=' setup.py | cut -d'"' -f2)"; \
	new_version="$$(echo "$${current_version}" | awk -F. '{$$NF = $$NF + 1;} 1' | sed 's/ /./g')"; \
	sed -i "s/version=\"$${current_version}\"/version=\"$${new_version}\"/" setup.py; \
	echo "📈 Version bumped from $${current_version} to $${new_version}"

bump-minor:
	@echo "🔢 Bumping minor version..."
	@current_version="$$(grep 'version=' setup.py | cut -d'"' -f2)"; \
	new_version="$$(echo "$${current_version}" | awk -F. '{$$(NF-1) = $$(NF-1) + 1; $$NF = 0;} 1' | sed 's/ /./g')"; \
	sed -i "s/version=\"$${current_version}\"/version=\"$${new_version}\"/" setup.py; \
	echo "📈 Version bumped from $${current_version} to $${new_version}"

bump-major:
	@echo "🔢 Bumping major version..."
	@current_version="$$(grep 'version=' setup.py | cut -d'"' -f2)"; \
	new_version="$$(echo "$${current_version}" | awk -F. '{$$(NF-2) = $$(NF-2) + 1; $$(NF-1) = 0; $$NF = 0;} 1' | sed 's/ /./g')"; \
	sed -i "s/version=\"$${current_version}\"/version=\"$${new_version}\"/" setup.py; \
	echo "📈 Version bumped from $${current_version} to $${new_version}"

