# GAINS Food Vision API - Makefile

.PHONY: help setup-validate install dev test clean

help:
	@echo "GAINS Food Vision API - Available Commands"
	@echo "==========================================="
	@echo ""
	@echo "  make setup-validate  - One-command setup + validation (RECOMMENDED)"
	@echo "  make install        - Install Python dependencies"
	@echo "  make dev            - Start development server"
	@echo "  make test           - Run test suite"
	@echo "  make clean          - Clean build artifacts"
	@echo ""

setup-validate:
	@chmod +x scripts/setup_and_validate.sh
	@./scripts/setup_and_validate.sh

install:
	@echo "📦 Installing dependencies..."
	@pip install -r requirements.txt

dev:
	@echo "🚀 Starting development server..."
	@uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "🧪 Running tests..."
	@pytest tests/ -v

clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf __pycache__ .pytest_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Clean complete"
