.PHONY: help install install-dev format lint test

help: ## 📋 Show available targets and current settings
	@echo "✨ PlomTTS 🗣️"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*##/ { printf "  %-15s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## 📦 Install dependencies (server and client)
	pip install -r client/requirements.txt
	pip install -r server/requirements.txt

install-dev: install ## 🔧 Install dev tools (linter, testing)
	pip install -r requirements-dev.txt

format: ## ✨ Format code with black and isort
	@echo "✨ Formatting code..."
	black .
	isort .
	@echo "✅ Code formatted"

lint: ## 🎨 Run comprehensive linting checks
	@echo "🎨 Running linting checks..."
	black --check .
	isort --check-only .
	pylint --recursive=y .
	mypy .
	@echo "✅ All linting checks complete"

test: ## 🧪 Run tests
	cd client && make test
