.PHONY: setup test test-e2e eval eval-text eval-multi run build docker help verify-live verify-submission verify-sources frontend-test frontend-typecheck demo-gate calibration

# Python launcher: `python3` where it is a real interpreter (Linux/mac/CI),
# `python` on Windows — the MS Store `python3` stub fails the -c probe, so
# `make verify-live` etc. work unchanged on the demo laptop.
PY := $(shell python3 -c "print('python3')" 2>/dev/null || echo python)

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup:  ## Install all dependencies
	pip install -r backend/requirements.txt
	pip install pytest pytest-cov
	cd frontend && npm install

corpus:  ## Generate all project corpora (12 projects, 50 deviations)
	$(PY) data/generate_corpus.py
	$(PY) data/generate_projects.py

test:  ## Run the full test suite
	$(PY) -m pytest tests/ -q

test-cov:  ## Run tests with coverage report
	$(PY) -m pytest tests/ --cov=backend --cov-report=term-missing -q

test-e2e:  ## Run the Playwright E2E suite (upload, paste, evidence links, keyboard nav, mobile)
	cd frontend && npx playwright test

calibration:  ## Regenerate the benchmark's stratified confidence-interval report
	$(PY) scripts/benchmark_calibration.py

eval:  ## Run baseline eval (P/R/F1)
	$(PY) eval/run_eval.py --detector baseline

eval-text:  ## Run non-circular text eval (raw markdown → regex)
	$(PY) eval/text_eval.py

eval-multi:  ## Run multi-project eval (12 projects, 11 countries)
	$(PY) eval/multi_project_eval.py

eval-multi-llm:  ## Run REAL LLM eval across all 12 projects (needs API key)
	$(PY) eval/multi_project_eval.py --detector llm

eval-real:  ## LLM layer over the real-datasheet pairs (needs API key; ~14 calls)
	$(PY) eval/real_pairs_llm.py

eval-all:  ## Run all three eval paths
	@echo "=== Baseline Eval ===" && $(PY) eval/run_eval.py --detector baseline
	@echo "\n=== Text Eval ===" && $(PY) eval/text_eval.py
	@echo "\n=== Multi-Project Eval ===" && $(PY) eval/multi_project_eval.py

run:  ## Start backend API (localhost:8000)
	uvicorn backend.main:app --reload

run-frontend:  ## Start frontend (localhost:3000)
	cd frontend && npm run dev

docker:  ## Launch full stack via Docker Compose
	docker compose up --build

lint:  ## Run Python linting
	$(PY) -m py_compile backend/main.py
	$(PY) -m py_compile backend/orchestrator.py
	$(PY) -m py_compile backend/analyze.py
	$(PY) -m py_compile eval/run_eval.py
	$(PY) -m py_compile eval/text_eval.py
	$(PY) -m py_compile eval/multi_project_eval.py
	@echo "All Python files compile clean"

verify-ocr:  ## Prove OCR works locally (skips cleanly if tesseract absent)
	$(PY) scripts/verify_ocr.py

verify-ocr-docker:  ## Prove OCR works in the shipping backend image (needs Docker)
	sh scripts/verify_ocr_docker.sh

verify:  ## One-command verification: tests + calibration + evals + frontend checks
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║  PRAMAAN — Full Verification Suite                         ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "▸ [1/6] Running full test suite..."
	$(PY) -m pytest tests/ -q --tb=short
	@echo ""
	@echo "▸ [2/6] Calibration report is up to date..."
	$(PY) scripts/benchmark_calibration.py
	@echo ""
	@echo "▸ [3/6] Baseline eval (Meghdoot, 14 devs)..."
	$(PY) eval/run_eval.py
	@echo ""
	@echo "▸ [4/6] Text-based eval (non-circular)..."
	$(PY) eval/text_eval.py
	@echo ""
	@echo "▸ [5/6] Multi-project eval (12 projects, 50 devs)..."
	$(PY) eval/multi_project_eval.py
	@echo ""
	@echo "▸ [6/6] Frontend type check, component tests, audit, build..."
	cd frontend && npm run typecheck
	cd frontend && npm test
	cd frontend && npm audit && npm run build
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║  ✓ ALL CHECKS PASSED                                      ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"

demo-gate:  ## Pre-judge gate: repo checks, security, E2E, frontend checks, live health; video handled separately
	$(PY) -m ruff check .
	$(PY) -m pip_audit --local
	$(PY) -m bandit -r backend/ scripts/ --severity-level medium
	$(PY) -m pytest tests/ -q --tb=short
	$(PY) scripts/check_claim_counts.py
	$(PY) scripts/benchmark_manifest_check.py
	$(PY) scripts/benchmark_hash_sources.py
	$(PY) scripts/benchmark_calibration.py
	cd frontend && npm test
	cd frontend && npm run typecheck
	cd frontend && npm audit --audit-level=moderate
	cd frontend && npm run build
	cd frontend && npx playwright test
	$(PY) scripts/verify_live.py

build:  ## Build frontend for production
	cd frontend && npm run build

frontend-typecheck:  ## Run strict frontend TypeScript checks
	cd frontend && npm run typecheck

frontend-test:  ## Run frontend component tests
	cd frontend && npm test

verify-live:  ## Pre-demo gate: is the DEPLOYED stack demo-ready right now?
	$(PY) scripts/verify_live.py

verify-sources:  ## Re-check public real-sample provenance URLs
	$(PY) scripts/check_real_source_links.py

verify-submission:  ## Final Unstop gate: fail if mandatory submission placeholders remain
	$(PY) scripts/check_submission_ready.py
