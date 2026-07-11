"""
In-process job + result-cache layer — a PROTOTYPE-level scalability proof.

This is deliberately NOT a production queue. Everything is in-memory, bounded,
and single-instance:

- **Idempotency / caching by input hash** so an identical analysis is computed
  once; concurrent duplicates are coalesced (single-flight), cutting both LLM
  quota and latency. `cached=true` reports a reused result.
- **A tiny async-style job flow** (submit → poll status → fetch result) that
  demonstrates non-blocking handling without a broker or database.

Bounds (LRU + TTL) keep memory flat. A restart or a second replica loses this
state — production would use Redis + a worker queue + a persistent store (see
`docs/SCALABILITY_PROOF.md`). **No secrets and no raw uploaded bytes are cached**
— only the computed deviation result plus non-sensitive metadata (hashes,
timings, status). The input hash is SHA-256 and one-way; it is not reversible to
the document text.
"""

import concurrent.futures
import hashlib
import os
import threading
import time
import uuid
from collections import OrderedDict

from backend.analyze import run_analysis

# Bump when SYSTEM_PROMPT / PROMPT_TEMPLATE change so cached results from an old
# prompt are not reused under a new one (part of the input-hash "config version").
PROMPT_VERSION = "reconcile-v2"


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (ValueError, TypeError):
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (ValueError, TypeError):
        return default


_CACHE_TTL_S = _float_env("PRAMAAN_CACHE_TTL_S", 3600)
# Degraded (non-LLM) results get a much shorter TTL. The demo pair is a FIXED
# input, so caching a rule-floor fallback under the full TTL would pin every
# subsequent identical request to the degraded answer for up to an hour after
# one transient 429 — long after the LLM recovered. Recomputing a rule-floor
# result is instant and quota-free, so a short TTL costs nothing.
_DEGRADED_TTL_S = _float_env("PRAMAAN_DEGRADED_CACHE_TTL_S", 120)
_CACHE_MAX = _int_env("PRAMAAN_CACHE_MAX", 256)
_JOB_MAX = _int_env("PRAMAAN_JOB_MAX", 256)
_MAX_WORKERS = _int_env("PRAMAAN_JOB_WORKERS", 2)


# ── input hashing / pipeline signature ──────────────────────────────

def pipeline_signature() -> str:
    """Short, non-secret signature of the analysis pipeline config, folded into
    the input hash so a model/prompt change invalidates cached results."""
    primary = os.getenv("PRAMAAN_LLM", "gemini").lower()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return f"{primary}:{model}:{PROMPT_VERSION}"


def compute_input_hash(spec: str, submittal: str, system_id: str = "CUSTOM") -> str:
    """sha256(owner_doc + vendor_doc + system + config/model/prompt version).
    One-way — never stored alongside, or reversible to, the document text."""
    h = hashlib.sha256()
    for part in (spec or "", "\x00", submittal or "", "\x00",
                 system_id or "", "\x00", pipeline_signature()):
        h.update(part.encode("utf-8", "replace"))
    return h.hexdigest()


def new_request_id() -> str:
    return uuid.uuid4().hex


def valid_job_id(job_id: str) -> bool:
    return isinstance(job_id, str) and len(job_id) == 32 and all(
        c in "0123456789abcdef" for c in job_id)


# ── result cache (LRU + TTL) with single-flight ─────────────────────

_cache: "OrderedDict[str, dict]" = OrderedDict()
_cache_lock = threading.Lock()
_hash_locks: dict[str, threading.Lock] = {}
_hash_locks_guard = threading.Lock()


def _cache_get(h: str):
    now = time.time()
    with _cache_lock:
        entry = _cache.get(h)
        if entry is None:
            return None
        if now - entry["computed_at"] > entry.get("ttl_s", _CACHE_TTL_S):
            _cache.pop(h, None)
            return None
        _cache.move_to_end(h)
        return entry


def _cache_put(h: str, entry: dict) -> None:
    with _cache_lock:
        _cache[h] = entry
        _cache.move_to_end(h)
        while len(_cache) > _CACHE_MAX:
            _cache.popitem(last=False)


def _lock_for(h: str) -> threading.Lock:
    with _hash_locks_guard:
        if len(_hash_locks) > _CACHE_MAX * 2:
            # Drop idle (unlocked) hash locks so this dict can't grow without
            # bound. A rare race here only costs a redundant recompute — the
            # post-lock cache re-check keeps results correct.
            for k in [k for k, lk in list(_hash_locks.items()) if not lk.locked()]:
                _hash_locks.pop(k, None)
        return _hash_locks.setdefault(h, threading.Lock())


def _view(h: str, entry: dict, cached: bool) -> dict:
    return {
        "input_hash": h,
        "cached": cached,
        "deviations": entry["deviations"],
        "count": entry["count"],
        "mode": entry["mode"],
        "elapsed_ms": entry["elapsed_ms"],
        # Stage-level breakdown of elapsed_ms + which failover-chain provider
        # actually answered — cached alongside the result, so a cache hit
        # still reports how long the underlying analysis originally took
        # rather than the near-zero cache-lookup time.
        "timing": {
            "standards_load_ms": entry.get("standards_load_ms", 0),
            "llm_call_ms": entry.get("llm_call_ms"),
            "postprocess_ms": entry.get("postprocess_ms", 0),
            "provider": entry.get("provider"),
        },
    }


def analyze_cached(spec: str, submittal: str, system_id: str = "CUSTOM") -> dict:
    """Run the analysis once per unique input hash, coalescing concurrent
    duplicates (single-flight). Returns the deviation view with `cached` and
    `input_hash`. Never caches secrets — only the deviation result + metadata."""
    h = compute_input_hash(spec, submittal, system_id)
    hit = _cache_get(h)
    if hit is not None:
        return _view(h, hit, cached=True)
    with _lock_for(h):
        hit = _cache_get(h)  # another thread may have computed it while we waited
        if hit is not None:
            return _view(h, hit, cached=True)
        res = run_analysis(spec, submittal, system_id)
        entry = {
            "deviations": res.deviations,
            "count": len(res.deviations),
            "mode": res.mode,
            "elapsed_ms": res.elapsed_ms,
            "standards_load_ms": res.standards_load_ms,
            "llm_call_ms": res.llm_call_ms,
            "postprocess_ms": res.postprocess_ms,
            "provider": res.provider,
            "computed_at": time.time(),
            # LLM-backed results keep the full TTL; a degraded (rule-floor /
            # vision-unavailable) result expires fast so it can never pin an
            # identical input to the fallback after the provider recovers.
            "ttl_s": (_CACHE_TTL_S if res.mode in ("llm", "vision")
                      else min(_CACHE_TTL_S, _DEGRADED_TTL_S)),
        }
        _cache_put(h, entry)
        return _view(h, entry, cached=False)


# ── job flow (submit → poll → result) ───────────────────────────────

_jobs: "OrderedDict[str, dict]" = OrderedDict()
_jobs_lock = threading.Lock()
_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=_MAX_WORKERS, thread_name_prefix="pramaan-job")

_STATUS_FIELDS = ("job_id", "request_id", "input_hash", "status", "submitted_at",
                  "started_at", "finished_at", "latency_ms", "mode", "count",
                  "cached", "error")


def submit_job(spec: str, submittal: str, system_id: str, request_id: str) -> dict:
    """Enqueue an analysis job on the bounded worker pool; returns immediately
    with the queued job record (status metadata, no result yet)."""
    job_id = uuid.uuid4().hex
    job = {
        "job_id": job_id, "request_id": request_id,
        "input_hash": compute_input_hash(spec, submittal, system_id),
        "status": "queued", "submitted_at": time.time(),
        "started_at": None, "finished_at": None, "latency_ms": None,
        "mode": None, "count": None, "cached": None, "error": None,
        "_result": None,
    }
    with _jobs_lock:
        _jobs[job_id] = job
        while len(_jobs) > _JOB_MAX:
            _jobs.popitem(last=False)
        # Snapshot the queued state BEFORE dispatching, so the submit response is
        # deterministically "queued" and never races the worker's status update.
        snapshot = {k: job[k] for k in _STATUS_FIELDS}
    _pool.submit(_run_job, job_id, spec, submittal, system_id)
    return snapshot


def _run_job(job_id: str, spec: str, submittal: str, system_id: str) -> None:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return
        job["status"] = "running"
        job["started_at"] = time.time()
    try:
        view = analyze_cached(spec, submittal, system_id)
        with _jobs_lock:
            job = _jobs.get(job_id)
            if job is None:
                return
            job.update(status="done", finished_at=time.time(),
                       mode=view["mode"], count=view["count"],
                       cached=view["cached"], _result=view,
                       latency_ms=round((time.time() - job["started_at"]) * 1000))
    except Exception:  # run_analysis is itself resilient; this is belt-and-braces
        with _jobs_lock:
            job = _jobs.get(job_id)
            if job is not None:
                job.update(status="error", finished_at=time.time(),
                           error="analysis failed")  # generic — never leak internals


def job_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        return None if job is None else {k: job[k] for k in _STATUS_FIELDS}


def job_result(job_id: str):
    """Returns (status, result_view|None). status is None for an unknown id."""
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            return None, None
        return job["status"], job.get("_result")


def stats() -> dict:
    """Non-sensitive counters for /health-style status."""
    with _cache_lock:
        cache_n = len(_cache)
    with _jobs_lock:
        jobs_n = len(_jobs)
    return {"cache_entries": cache_n, "cache_max": _CACHE_MAX,
            "jobs_tracked": jobs_n, "job_workers": _MAX_WORKERS,
            "pipeline_signature": pipeline_signature()}


def reset() -> None:
    """Clear all in-memory state — used by the test suite between cases."""
    with _cache_lock:
        _cache.clear()
    with _jobs_lock:
        _jobs.clear()
    with _hash_locks_guard:
        _hash_locks.clear()
