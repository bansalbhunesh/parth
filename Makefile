.PHONY: setup test eval eval-text eval-multi run build docker help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup:  ## Install all dependencies
	pip install -r backend/requirements.txt
	pip install pytest pytest-cov
	cd frontend && npm install

corpus:  ## Generate all project corpora (12 projects, 50 deviations)
	python3 data/generate_corpus.py
	python3 data/generate_projects.py

test:  ## Run 250-test suite
	python3 -m pytest tests/ -q

test-cov:  ## Run tests with coverage report
	python3 -m pytest tests/ --cov=backend --cov-report=term-missing -q

eval:  ## Run baseline eval (P/R/F1)
	python3 eval/run_eval.py --detector baseline

eval-text:  ## Run non-circular text eval (raw markdown → regex)
	python3 eval/text_eval.py

eval-multi:  ## Run multi-project eval (6 projects, 5 countries)
	python3 eval/multi_project_eval.py

eval-all:  ## Run all three eval paths
	@echo "=== Baseline Eval ===" && python3 eval/run_eval.py --detector baseline
	@echo "\n=== Text Eval ===" && python3 eval/text_eval.py
	@echo "\n=== Multi-Project Eval ===" && python3 eval/multi_project_eval.py

run:  ## Start backend API (localhost:8000)
	uvicorn backend.main:app --reload

run-frontend:  ## Start frontend (localhost:3000)
	cd frontend && npm run dev

docker:  ## Launch full stack via Docker Compose
	docker compose up --build

lint:  ## Run Python linting
	python3 -m py_compile backend/main.py
	python3 -m py_compile backend/orchestrator.py
	python3 -m py_compile backend/analyze.py
	python3 -m py_compile eval/run_eval.py
	python3 -m py_compile eval/text_eval.py
	python3 -m py_compile eval/multi_project_eval.py
	@echo "All Python files compile clean"

verify:  ## One-command verification: tests + all evals + frontend type check
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║  PRAMAAN — Full Verification Suite                         ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "▸ [1/5] Running 250-test suite..."
	python3 -m pytest tests/ -q --tb=short
	@echo ""
	@echo "▸ [2/5] Baseline eval (Meghdoot, 14 devs)..."
	python3 eval/run_eval.py
	@echo ""
	@echo "▸ [3/5] Text-based eval (non-circular)..."
	python3 eval/text_eval.py
	@echo ""
	@echo "▸ [4/5] Multi-project eval (6 projects, 33 devs)..."
	python3 eval/multi_project_eval.py
	@echo ""
	@echo "▸ [5/5] Frontend type check..."
	cd frontend && npx tsc --noEmit
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║  ✓ ALL CHECKS PASSED                                      ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"

build:  ## Build frontend for production
	cd frontend && npm run build
