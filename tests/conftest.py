"""Shared test fixtures / default test posture for the whole suite.

The public-demo security controls (token auth + rate limiting) default to a
production-friendly posture (rate limiting ON). For the test suite — which
deliberately hammers the expensive endpoints — we force them OFF so the
existing behavioural tests are unaffected. Tests that specifically exercise
auth or rate limiting opt back in with monkeypatch.setenv(...).
"""

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Force the safe test posture BEFORE any test module imports the app. Security
# config is read per-request, so this fully governs behaviour unless a test
# overrides it via monkeypatch.
os.environ["DEMO_AUTH_ENABLED"] = "false"
os.environ["PRAMAAN_RATE_LIMIT_ENABLED"] = "0"


@pytest.fixture(autouse=True)
def _reset_process_state():
    """Clear the process-local rate-limit counters, the job/result cache, AND
    the per-provider LLM budget counters around every test so none leaks
    between cases (all share one in-process store)."""
    from backend import jobs, llm, security
    security.reset_rate_limits()
    jobs.reset()
    llm.reset_budgets()
    yield
    security.reset_rate_limits()
    jobs.reset()
    llm.reset_budgets()
