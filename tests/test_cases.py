"""Case store: persisted, tenant-isolated submittal -> RFI -> audit-log
workflow (the "deepen one production workflow" addition).

Proves the reliability/security contract: a case's data is invisible without
its exact secret, a wrong secret 404s identically to a nonexistent case (no
existence oracle), findings/RFIs persist and are scoped per case, RFI
drafting degrades to an offline template with no LLM configured, and the
audit log records every write without ever storing the raw secret.
"""

from fastapi.testclient import TestClient

from backend import case_store
from backend.main import app

client = TestClient(app)

_FINDING = {
    "component": "UPS-02", "parameter": "battery_runtime_min",
    "required_value": "10", "provided_value": "7", "unit": "min",
    "severity": "Critical", "standard_ref": "UPTIME-TIER4",
    "spec_clause": "DB-4.3", "predicted_cx_test": "IST-07",
    "lead_time_weeks": 27, "rationale": "Battery autonomy below requirement.",
}


def _no_llm(monkeypatch):
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "QWEN_GATEWAY_API_KEY",
              "GROQ_API_KEY", "ANTHROPIC_API_KEY", "CLAUDE_API_KEY",
              "LOCAL_LLM_ENABLED"):
        monkeypatch.delenv(k, raising=False)


def _create_case(name="Test Case"):
    r = client.post("/cases", json={"name": name})
    assert r.status_code == 200
    body = r.json()
    assert body["case_id"] and body["secret"]
    return body["case_id"], body["secret"]


def test_create_case_returns_id_and_secret():
    case_id, secret = _create_case()
    assert len(case_id) == 32
    assert len(secret) > 20


def test_case_is_invisible_without_the_secret():
    case_id, secret = _create_case()
    r = client.get(f"/cases/{case_id}")  # no X-Case-Secret header
    assert r.status_code == 404


def test_wrong_secret_404s_identically_to_nonexistent_case():
    case_id, secret = _create_case()
    wrong = client.get(f"/cases/{case_id}", headers={"X-Case-Secret": "not-the-secret"})
    missing = client.get("/cases/ffffffffffffffffffffffffffffffff",
                         headers={"X-Case-Secret": "irrelevant"})
    assert wrong.status_code == missing.status_code == 404
    assert wrong.json()["detail"] == missing.json()["detail"]


def test_correct_secret_reads_the_case():
    case_id, secret = _create_case("Project Meridian")
    r = client.get(f"/cases/{case_id}", headers={"X-Case-Secret": secret})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Project Meridian"
    assert body["findings_count"] == 0
    assert body["rfis_count"] == 0


def test_add_and_list_findings_scoped_to_case():
    case_a, secret_a = _create_case("A")
    case_b, secret_b = _create_case("B")
    hdr_a = {"X-Case-Secret": secret_a}
    hdr_b = {"X-Case-Secret": secret_b}

    r = client.post(f"/cases/{case_a}/findings", json=_FINDING, headers=hdr_a)
    assert r.status_code == 200
    finding_id = r.json()["finding_id"]
    assert finding_id

    # Case A sees it.
    found_a = client.get(f"/cases/{case_a}/findings", headers=hdr_a).json()["findings"]
    assert len(found_a) == 1
    assert found_a[0]["component"] == "UPS-02"

    # Case B does not — tenant isolation, not just secret-gating.
    found_b = client.get(f"/cases/{case_b}/findings", headers=hdr_b).json()["findings"]
    assert found_b == []

    # Case B's secret cannot read case A's findings even if it guesses the id.
    cross = client.get(f"/cases/{case_a}/findings", headers=hdr_b)
    assert cross.status_code == 404


def test_finding_not_found_on_this_case_404s():
    case_id, secret = _create_case()
    r = client.post(f"/cases/{case_id}/findings/{'0' * 32}/rfi",
                    headers={"X-Case-Secret": secret})
    assert r.status_code == 404


def test_draft_rfi_offline_fallback_with_no_llm_configured(monkeypatch):
    _no_llm(monkeypatch)
    case_id, secret = _create_case()
    hdr = {"X-Case-Secret": secret}
    finding_id = client.post(f"/cases/{case_id}/findings", json=_FINDING,
                             headers=hdr).json()["finding_id"]

    r = client.post(f"/cases/{case_id}/findings/{finding_id}/rfi", headers=hdr)
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "offline-fallback"
    assert "UPS-02" in body["drafted_text"]
    assert "10" in body["drafted_text"] and "7" in body["drafted_text"]

    rfis = client.get(f"/cases/{case_id}/rfis", headers=hdr).json()["rfis"]
    assert len(rfis) == 1
    assert rfis[0]["rfi_id"] == body["rfi_id"]


def test_export_rfi_renders_html(monkeypatch):
    _no_llm(monkeypatch)
    case_id, secret = _create_case("Export Test")
    hdr = {"X-Case-Secret": secret}
    finding_id = client.post(f"/cases/{case_id}/findings", json=_FINDING,
                             headers=hdr).json()["finding_id"]
    rfi_id = client.post(f"/cases/{case_id}/findings/{finding_id}/rfi",
                         headers=hdr).json()["rfi_id"]

    r = client.get(f"/cases/{case_id}/rfis/{rfi_id}/export", headers=hdr)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "UPS-02" in r.text
    assert "Export Test" in r.text


def test_export_unknown_rfi_404s():
    case_id, secret = _create_case()
    r = client.get(f"/cases/{case_id}/rfis/{'0' * 32}/export",
                   headers={"X-Case-Secret": secret})
    assert r.status_code == 404


def test_audit_log_records_actions_without_storing_the_raw_secret(monkeypatch):
    _no_llm(monkeypatch)
    case_id, secret = _create_case("Audited Case")
    hdr = {"X-Case-Secret": secret}
    finding_id = client.post(f"/cases/{case_id}/findings", json=_FINDING,
                             headers=hdr).json()["finding_id"]
    client.post(f"/cases/{case_id}/findings/{finding_id}/rfi", headers=hdr)

    log = client.get(f"/cases/{case_id}/audit-log", headers=hdr).json()["audit_log"]
    actions = [entry["action"] for entry in log]
    assert actions == ["case_created", "finding_added", "rfi_drafted"]
    for entry in log:
        assert secret not in entry["actor_key"]
        assert entry["actor_key"] != secret
        assert len(entry["actor_key"]) == 12  # sha256(secret)[:12], never the raw secret


def test_audit_log_is_tenant_isolated():
    case_a, secret_a = _create_case("A")
    case_b, secret_b = _create_case("B")
    log_a = client.get(f"/cases/{case_a}/audit-log",
                       headers={"X-Case-Secret": secret_a}).json()["audit_log"]
    log_b = client.get(f"/cases/{case_b}/audit-log",
                       headers={"X-Case-Secret": secret_b}).json()["audit_log"]
    # Each case only ever sees its own single "case_created" entry, not the
    # other case's.
    assert len(log_a) == 1 and len(log_b) == 1
    assert log_a != log_b


def test_case_store_actor_key_is_deterministic_and_non_reversible():
    key1 = case_store.actor_key_for("some-secret-value")
    key2 = case_store.actor_key_for("some-secret-value")
    key3 = case_store.actor_key_for("a-different-secret")
    assert key1 == key2
    assert key1 != key3
    assert "some-secret-value" not in key1
    assert len(key1) == 12
