# 🛡️ Diana Bot Protection Testing Makefile
# Easy commands for running the complete testing protection network

.PHONY: help test-all test-quick test-mvp test-cinema test-journey test-performance test-coverage clean install-deps

# Default target
.DEFAULT_GOAL := help

# Colors
CYAN=\033[0;36m
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## 🛡️ Show this help message
	@echo "$(CYAN)🛡️ Diana Bot Testing Protection Network$(NC)"
	@echo "$(CYAN)=====================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make test-all          # Run complete protection test suite"
	@echo "  make test-quick        # Quick smoke test only" 
	@echo "  make test-mvp          # MVP baseline protection tests"
	@echo "  make test-coverage     # Full tests with coverage report"

install-deps: ## 📦 Install all testing dependencies
	@echo "$(CYAN)📦 Installing testing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-timeout psutil
	pip install coverage[toml] pytest-mock pytest-benchmark
	@echo "$(GREEN)✅ Dependencies installed successfully!$(NC)"

test-env-check: ## 🔍 Check test environment setup
	@echo "$(CYAN)🔍 Checking test environment...$(NC)"
	@python3 -c "import pytest; print('✅ pytest available')" || (echo "$(RED)❌ pytest not found$(NC)" && exit 1)
	@python3 -c "import pytest_asyncio; print('✅ pytest-asyncio available')" || (echo "$(RED)❌ pytest-asyncio not found$(NC)" && exit 1)
	@test -d tests/protection || (echo "$(RED)❌ Protection tests directory not found$(NC)" && exit 1)
	@echo "$(GREEN)✅ Test environment ready!$(NC)"

test-quick: test-env-check ## 🚀 Run quick smoke test to verify environment
	@echo "$(CYAN)🚀 Running quick smoke test...$(NC)"
	./scripts/test_protection.sh quick
	@echo "$(GREEN)🚀 Quick smoke test completed!$(NC)"

test-mvp: test-env-check ## 🛡️ Run MVP baseline protection tests
	@echo "$(CYAN)🛡️ Running MVP baseline protection tests...$(NC)"
	./scripts/test_protection.sh mvp
	@echo "$(GREEN)🛡️ MVP protection tests completed!$(NC)"

test-cinema: test-env-check ## 🎬 Run cinema architecture integration tests
	@echo "$(CYAN)🎬 Running cinema architecture integration tests...$(NC)"
	./scripts/test_protection.sh cinema
	@echo "$(GREEN)🎬 Cinema architecture tests completed!$(NC)"

test-journey: test-env-check ## 🎭 Run user journey & archetype tests
	@echo "$(CYAN)🎭 Running user journey & archetype tests...$(NC)"
	./scripts/test_protection.sh journey
	@echo "$(GREEN)🎭 User journey tests completed!$(NC)"

test-performance: test-env-check ## ⚡ Run performance & scalability tests
	@echo "$(CYAN)⚡ Running performance & scalability tests...$(NC)"
	./scripts/test_protection.sh performance
	@echo "$(GREEN)⚡ Performance tests completed!$(NC)"

test-all: test-env-check ## 🛡️ Run complete protection test suite
	@echo "$(CYAN)🛡️ Running COMPLETE protection test suite...$(NC)"
	./scripts/test_protection.sh all
	@echo "$(GREEN)🛡️ Complete protection test suite finished!$(NC)"

test-coverage: test-env-check ## 📊 Run all tests with coverage report
	@echo "$(CYAN)📊 Running all tests with coverage report...$(NC)"
	./scripts/test_protection.sh coverage
	@echo "$(GREEN)📊 Coverage testing completed!$(NC)"

test-fail-fast: test-env-check ## 🚨 Run tests with fail-fast (stop on first critical failure)
	@echo "$(CYAN)🚨 Running tests with fail-fast mode...$(NC)"
	./scripts/test_protection.sh all --fail-fast
	@echo "$(GREEN)🚨 Fail-fast testing completed!$(NC)"

clean: ## 🧹 Clean test artifacts and cache files
	@echo "$(CYAN)🧹 Cleaning test artifacts...$(NC)"
	rm -rf logs/
	rm -rf test_reports/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -f .coverage
	rm -f coverage.xml
	@echo "$(GREEN)🧹 Cleanup completed!$(NC)"

test-watch: test-env-check ## 👀 Watch for changes and run quick tests
	@echo "$(CYAN)👀 Watching for changes (Ctrl+C to stop)...$(NC)"
	@while true; do \
		echo "$(YELLOW)⏱️  Waiting for changes...$(NC)"; \
		inotifywait -r -e modify --include=".*\.py$$" services/ database/ handlers/ tests/ 2>/dev/null || sleep 5; \
		echo "$(CYAN)🔄 Changes detected, running quick test...$(NC)"; \
		make test-quick || true; \
		echo "$(YELLOW)================================$(NC)"; \
		sleep 2; \
	done

test-docker: ## 🐳 Run tests in Docker container (if Docker is available)
	@if command -v docker >/dev/null 2>&1; then \
		echo "$(CYAN)🐳 Running tests in Docker container...$(NC)"; \
		docker run --rm -v $(PWD):/app -w /app python:3.10 bash -c "pip install -r requirements.txt && make test-all"; \
	else \
		echo "$(RED)❌ Docker not available, skipping Docker tests$(NC)"; \
	fi

test-benchmarks: test-env-check ## 📈 Run performance benchmarks
	@echo "$(CYAN)📈 Running performance benchmarks...$(NC)"
	python -m pytest tests/protection/test_performance_scalability.py::TestResponseTimeGuarantee --benchmark-only -v
	@echo "$(GREEN)📈 Performance benchmarks completed!$(NC)"

test-stress: test-env-check ## 💪 Run stress tests for scalability limits
	@echo "$(CYAN)💪 Running stress tests...$(NC)"
	python -m pytest tests/protection/test_performance_scalability.py::TestScalabilityBoundaries -v --timeout=300
	@echo "$(GREEN)💪 Stress tests completed!$(NC)"

test-critical: test-env-check ## 🚨 Run only critical protection tests
	@echo "$(CYAN)🚨 Running critical protection tests only...$(NC)"
	python -m pytest tests/protection/ -k "critical or smoke" -v
	@echo "$(GREEN)🚨 Critical tests completed!$(NC)"

test-debug: test-env-check ## 🐛 Run tests in debug mode with verbose output
	@echo "$(CYAN)🐛 Running tests in debug mode...$(NC)"
	./scripts/test_protection.sh all --verbose
	@echo "$(GREEN)🐛 Debug testing completed!$(NC)"

report: ## 📄 Generate and view latest test report
	@if [ -f "test_reports/latest_protection_report.json" ]; then \
		echo "$(CYAN)📄 Latest Test Report:$(NC)"; \
		python -c "import json; report = json.load(open('test_reports/latest_protection_report.json')); print(f\"Success Rate: {report['summary']['success_rate']}%\"); print(f\"Critical Success: {report['summary']['critical_success_rate']}%\")"; \
	else \
		echo "$(RED)❌ No test report found. Run tests first with: make test-all$(NC)"; \
	fi

status: ## 📊 Show current protection status
	@echo "$(CYAN)📊 Diana Bot Protection Status:$(NC)"
	@if [ -f "test_reports/latest_protection_report.json" ]; then \
		python -c "import json; report = json.load(open('test_reports/latest_protection_report.json')); protection = report['protection_status']; print(f\"MVP Baseline: {'🛡️ PROTECTED' if protection['mvp_baseline_protected'] else '🚨 VULNERABLE'}\"); print(f\"Cinema Architecture: {'🎬 PROTECTED' if protection['cinema_architecture_protected'] else '🚨 VULNERABLE'}\"); print(f\"User Journeys: {'🎭 PROTECTED' if protection['user_journeys_protected'] else '🚨 VULNERABLE'}\"); print(f\"Performance: {'⚡ GUARANTEED' if protection['performance_guaranteed'] else '🚨 AT RISK'}\")"; \
	else \
		echo "$(YELLOW)⚠️  No protection status available. Run tests first.$(NC)"; \
	fi

# Development shortcuts
dev-test: test-quick ## 🔧 Development shortcut: quick test
	@echo "$(GREEN)🔧 Development testing completed!$(NC)"

ci-test: test-all ## 🤖 CI/CD shortcut: complete test suite
	@echo "$(GREEN)🤖 CI testing completed!$(NC)"

pre-commit: test-quick test-critical ## 🚀 Pre-commit testing (quick + critical)
	@echo "$(GREEN)🚀 Pre-commit testing completed!$(NC)"

# Advanced targets
test-integration: test-mvp test-cinema ## 🔗 Run integration tests only
	@echo "$(GREEN)🔗 Integration testing completed!$(NC)"

test-unit: ## 🧪 Run unit tests from existing test suite
	@echo "$(CYAN)🧪 Running existing unit tests...$(NC)"
	python -m pytest tests/ -v --ignore=tests/protection/
	@echo "$(GREEN)🧪 Unit tests completed!$(NC)"

test-full: test-unit test-all ## 🎯 Run both unit and protection tests
	@echo "$(GREEN)🎯 Full testing suite completed!$(NC)"