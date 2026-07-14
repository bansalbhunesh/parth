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
    """Clear the process-local rate-limit counters, the job/result cache, the
    per-provider LLM budget counters, AND the persisted case store around
    every test so none leaks between cases (all share one process-local or
    on-disk store)."""
    from backend import case_store, jobs, llm, security
    from backend.platform.config import reset_platform_settings
    from backend.platform.identity import reset_identity_provider

    # Do not import the complete FastAPI application just to reset one legacy
    # collection.  Pulling every router into otherwise-isolated unit tests also
    # loads NumPy/PyMuPDF C extensions, slows collection, and prevents tools
    # such as Mutmut from safely replaying the suite in-process.  App-level
    # tests import ``backend.main`` during collection; tests that import it
    # later are covered by the post-test lookup below.
    def clear_webhooks_if_loaded():
        main_module = sys.modules.get("backend.main")
        if main_module is not None:
            main_module.SUBSCRIBED_WEBHOOKS.clear()

    reset_platform_settings()
    reset_identity_provider()
    security.reset_rate_limits()
    jobs.reset()
    llm.reset_budgets()
    case_store.reset()
    clear_webhooks_if_loaded()
    yield
    reset_platform_settings()
    reset_identity_provider()
    security.reset_rate_limits()
    jobs.reset()
    llm.reset_budgets()
    case_store.reset()
    clear_webhooks_if_loaded()
