"""
Case store — persisted, tenant-isolated project state for the
submittal -> RFI -> commissioning-risk workflow.

This is the one workflow this repo chose to deepen rather than add more
surface area to (see the external audit's P1-3 gap). Everything else in this
backend (jobs.py's result cache, the /projects/* fixture routes) is
deliberately in-memory or read-only static data; a "case" here is a real
record, backed by local storage, that a caller creates, owns via a bearer
secret, and comes back to.

**Honest scope, stated plainly, matching how jobs.py and security.py already
disclose their own limits:**
- SQLite on local disk. On the hosted Render deployment this survives
  restarts and redeploys *within the same running instance* only — Render's
  free-tier filesystem is not a persistent volume; a redeploy or a scale
  event wipes it. That is a real limitation, not a production guarantee, and
  is why this module's docstring says so instead of implying durability it
  doesn't have.
- "Tenant isolation" here means *per-case* isolation via a bearer secret
  issued at case creation — not real user accounts. There is still no
  concept of a user in this codebase (security.py confirms this: one shared
  demo token, no per-user identity). A case's secret is the closest thing to
  an owner identity, the same way security.py already treats a hashed token
  as the closest thing to a rate-limit identity.
- The audit trail records a *hash* of the presenting secret (never the
  secret itself, never reversible), following the exact pattern
  security.py already uses to bucket rate limits by token without ever
  storing the token.
"""

import hashlib
import logging
import os
import secrets
import sqlite3
import tempfile
import threading
import time
import uuid

log = logging.getLogger("pramaan.case_store")

_DB_PATH = os.getenv(
    "PRAMAAN_CASE_DB_PATH",
    os.path.join(tempfile.gettempdir(), "pramaan_cases.db"),
)

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    case_id     TEXT PRIMARY KEY,
    secret_hash TEXT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    created_at  REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS findings (
    finding_id        TEXT PRIMARY KEY,
    case_id           TEXT NOT NULL,
    component         TEXT NOT NULL DEFAULT '',
    parameter         TEXT NOT NULL DEFAULT '',
    required_value    TEXT NOT NULL DEFAULT '',
    provided_value    TEXT NOT NULL DEFAULT '',
    unit              TEXT NOT NULL DEFAULT '',
    severity          TEXT NOT NULL DEFAULT '',
    standard_ref      TEXT NOT NULL DEFAULT '',
    spec_clause       TEXT NOT NULL DEFAULT '',
    predicted_cx_test TEXT NOT NULL DEFAULT '',
    lead_time_weeks   REAL,
    rationale         TEXT NOT NULL DEFAULT '',
    created_at        REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS rfis (
    rfi_id        TEXT PRIMARY KEY,
    case_id       TEXT NOT NULL,
    finding_id    TEXT NOT NULL,
    question      TEXT NOT NULL DEFAULT '',
    drafted_text  TEXT NOT NULL DEFAULT '',
    sources       TEXT NOT NULL DEFAULT '[]',
    mode          TEXT NOT NULL DEFAULT '',
    created_at    REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id    TEXT NOT NULL,
    actor_key  TEXT NOT NULL,
    action     TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_findings_case ON findings(case_id);
CREATE INDEX IF NOT EXISTS idx_rfis_case ON rfis(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_case ON audit_log(case_id);
"""


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript(_SCHEMA)
        _conn.commit()
    return _conn


def actor_key_for(secret: str) -> str:
    """Non-reversible identity tag for the audit log — same hash-not-store
    pattern security.py uses for rate-limit buckets. Never the raw secret."""
    return hashlib.sha256((secret or "").encode()).hexdigest()[:12]


# ── cases ─────────────────────────────────────────────────────────────

def create_case(name: str = "") -> tuple[str, str]:
    """Create a new case. Returns (case_id, secret) — the secret is shown
    exactly once here and only its hash is ever stored; there is no recovery
    path if the caller loses it, by design (matches how a lost demo token
    cannot be recovered either)."""
    case_id = uuid.uuid4().hex
    secret = secrets.token_urlsafe(24)
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    with _lock:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO cases (case_id, secret_hash, name, created_at) VALUES (?, ?, ?, ?)",
            (case_id, secret_hash, (name or "")[:200], time.time()),
        )
        conn.commit()
    append_audit(case_id, actor_key_for(secret), "case_created", detail=name or "")
    return case_id, secret


def verify_case(case_id: str, secret: str) -> bool:
    """Constant-time secret check, gating every read/write to a case's data
    — this is the tenant-isolation boundary. A wrong or missing secret must
    look identical to a nonexistent case to the caller (no case-existence
    oracle via timing or error-message differences)."""
    with _lock:
        row = _get_conn().execute(
            "SELECT secret_hash FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()
    if row is None:
        return False
    return secrets.compare_digest(
        hashlib.sha256((secret or "").encode()).hexdigest(), row["secret_hash"]
    )


def case_summary(case_id: str) -> dict | None:
    with _lock:
        row = _get_conn().execute(
            "SELECT case_id, name, created_at FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()
    return dict(row) if row else None


# ── findings ──────────────────────────────────────────────────────────

_FINDING_FIELDS = (
    "component", "parameter", "required_value", "provided_value", "unit",
    "severity", "standard_ref", "spec_clause", "predicted_cx_test",
    "lead_time_weeks", "rationale",
)


# Static literal, not built from _FINDING_FIELDS at call time — an f-string
# INSERT (even over a fixed, non-user-controlled tuple) is exactly the shape
# Bandit's B608 rule flags, and this repo's own CI now gates on it. Spelling
# the column list out here instead is the actual fix, not a bypass comment.
_INSERT_FINDING_SQL = (
    "INSERT INTO findings (finding_id, case_id, component, parameter, "
    "required_value, provided_value, unit, severity, standard_ref, "
    "spec_clause, predicted_cx_test, lead_time_weeks, rationale, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


def add_finding(case_id: str, finding: dict) -> str:
    finding_id = uuid.uuid4().hex
    values = [finding.get(f) for f in _FINDING_FIELDS]
    with _lock:
        conn = _get_conn()
        conn.execute(_INSERT_FINDING_SQL, [finding_id, case_id, *values, time.time()])
        conn.commit()
    return finding_id


def list_findings(case_id: str) -> list[dict]:
    with _lock:
        rows = _get_conn().execute(
            "SELECT * FROM findings WHERE case_id = ? ORDER BY created_at", (case_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_finding(case_id: str, finding_id: str) -> dict | None:
    with _lock:
        row = _get_conn().execute(
            "SELECT * FROM findings WHERE case_id = ? AND finding_id = ?",
            (case_id, finding_id),
        ).fetchone()
    return dict(row) if row else None


# ── RFIs ──────────────────────────────────────────────────────────────

def add_rfi(case_id: str, finding_id: str, question: str, drafted_text: str,
            sources: list[str], mode: str) -> str:
    import json as _json
    rfi_id = uuid.uuid4().hex
    with _lock:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO rfis (rfi_id, case_id, finding_id, question, drafted_text, "
            "sources, mode, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (rfi_id, case_id, finding_id, question, drafted_text,
             _json.dumps(sources), mode, time.time()),
        )
        conn.commit()
    return rfi_id


def list_rfis(case_id: str) -> list[dict]:
    with _lock:
        rows = _get_conn().execute(
            "SELECT * FROM rfis WHERE case_id = ? ORDER BY created_at", (case_id,)
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        import json as _json
        try:
            d["sources"] = _json.loads(d["sources"])
        except (ValueError, TypeError):
            d["sources"] = []
        out.append(d)
    return out


def get_rfi(case_id: str, rfi_id: str) -> dict | None:
    with _lock:
        row = _get_conn().execute(
            "SELECT * FROM rfis WHERE case_id = ? AND rfi_id = ?", (case_id, rfi_id)
        ).fetchone()
    if row is None:
        return None
    d = dict(row)
    import json as _json
    try:
        d["sources"] = _json.loads(d["sources"])
    except (ValueError, TypeError):
        d["sources"] = []
    return d


# ── audit log ─────────────────────────────────────────────────────────

def append_audit(case_id: str, actor_key: str, action: str, detail: str = "") -> None:
    with _lock:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO audit_log (case_id, actor_key, action, detail, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (case_id, actor_key, action, (detail or "")[:500], time.time()),
        )
        conn.commit()


def get_audit_log(case_id: str) -> list[dict]:
    with _lock:
        rows = _get_conn().execute(
            "SELECT actor_key, action, detail, created_at FROM audit_log "
            "WHERE case_id = ? ORDER BY created_at", (case_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── test / lifecycle support ─────────────────────────────────────────

def reset() -> None:
    """Clear all persisted state — used by the test suite between cases, the
    same role jobs.reset() and security.reset_rate_limits() play. Four
    static DELETE statements, not a loop building an f-string — same B608
    reasoning as _INSERT_FINDING_SQL above."""
    with _lock:
        conn = _get_conn()
        conn.execute("DELETE FROM audit_log")
        conn.execute("DELETE FROM rfis")
        conn.execute("DELETE FROM findings")
        conn.execute("DELETE FROM cases")
        conn.commit()


def close() -> None:
    """Close the module-level connection — used when a test wants a fully
    fresh file (e.g. PRAMAAN_CASE_DB_PATH changed mid-run). Not used in
    normal request handling."""
    global _conn
    with _lock:
        if _conn is not None:
            _conn.close()
            _conn = None
