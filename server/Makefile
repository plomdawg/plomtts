# 🐳 PlomTTS Local Development Makefile
# Makefile for local development, testing, and Docker Compose management

.PHONY: help run stop logs clean dev test test-live

help: ## 📋 Show available targets
	@echo "🐳 PlomTTS Local Development"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*##/ { printf "  %-15s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "ℹ️  Docker images are automatically built and published via GitHub Actions"
	@echo "   Push to main branch or create a tag to trigger deployment"

run: ## ▶️ Run container locally for testing
	@echo "▶️ Running PlomTTS container locally..."
	@echo "🌐 Starting on port 8420..."
	docker compose up -d --build
	@echo "✅ Container started!"
	@echo "🔗 Access at: http://localhost:8420"
	@echo "📋 Use 'make logs' to see output"
	@echo "⏹️ Use 'make stop' to stop the container"

stop: ## ⏹️ Stop running containers
	@echo "⏹️ Stopping PlomTTS containers..."
	docker compose down
	@echo "✅ Containers stopped"

clean: ## 🧹 Clean up Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	docker compose down --volumes --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete"

logs: ## 📋 Show container logs
	@echo "📋 Showing PlomTTS container logs..."
	docker compose logs -f

dev: clean run ## 🔄 Complete local development setup
	@echo "🎉 Local development environment ready!"
	@echo "📋 Summary:"
	@echo "  - ✅ Cleaned up old resources"
	@echo "  - ✅ Started PlomTTS containers"
	@echo ""
	@echo "🔗 Access your application at:"
	@echo "   http://localhost:8420 (PlomTTS API)"
	@echo "   http://localhost:7860 (Fish Speech UI)"

test: ## 🧪 Run tests
	@echo "🧪 Running tests..."
	pytest tests/ --verbose -m "not live"
	@echo "✅ Tests complete"

test-live: ## 🌐 Run live integration tests
	@echo "🌐 Running live integration tests..."
	pytest tests/ --verbose -m live
	@echo "✅ Live tests complete"
