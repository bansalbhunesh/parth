"""Downstream RFI webhooks: subscribe / list / clear endpoints plus the
fan-out trigger that fires on Critical/Major findings.

Proves the safety contract added on top of the feature: only public http(s)
URLs can be subscribed (no SSRF into loopback/private/link-local/metadata
targets), the list is capped and never echoes a full subscriber URL back
(Slack webhook URLs are secrets), payloads are built defensively from
possibly-incomplete LLM dicts, and delivery failures never raise into the
analysis path. All tests are offline: hosts are numeric literals, so no DNS
lookup happens, and delivery is monkeypatched.
"""

import threading

from fastapi.testclient import TestClient

from backend import main
from backend.main import app

client = TestClient(app)

# Numeric public IP: getaddrinfo resolves it without a DNS query, so the
# suite stays offline-safe. Nothing is ever POSTed to it (delivery is
# monkeypatched in every trigger test).
_PUBLIC_URL = "http://8.8.8.8/hook"

_DEV = {
    "component": "UPS-02", "parameter": "battery_runtime_min",
    "required_value": "10", "provided_value": "7", "unit": "min",
    "severity": "Critical", "standard_ref": "UPTIME-TIER4",
    "spec_clause": "DB-4.3", "predicted_cx_test": "IST-07",
    "lead_time_weeks": 27, "rationale": "Battery autonomy below requirement.",
}


def _no_private_override(monkeypatch):
    monkeypatch.delenv("PRAMAAN_WEBHOOK_ALLOW_PRIVATE", raising=False)


# ── subscribe: validation ────────────────────────────────────────────

def test_subscribe_public_url_ok(monkeypatch):
    _no_private_override(monkeypatch)
    r = client.post("/webhooks/subscribe", json={"url": _PUBLIC_URL})
    assert r.status_code == 200
    assert r.json()["status"] == "subscribed"
    assert main.SUBSCRIBED_WEBHOOKS == [_PUBLIC_URL]


def test_subscribe_rejects_non_http_schemes(monkeypatch):
    _no_private_override(monkeypatch)
    for bad in ("ftp://8.8.8.8/x", "file:///etc/passwd", "not-a-url", "javascript:alert(1)"):
        r = client.post("/webhooks/subscribe", json={"url": bad})
        assert r.status_code == 400, bad
    assert main.SUBSCRIBED_WEBHOOKS == []


def test_subscribe_rejects_private_and_metadata_targets(monkeypatch):
    _no_private_override(monkeypatch)
    for bad in (
        "http://127.0.0.1/hook",             # loopback
        "http://localhost:8000/hook",        # loopback by name
        "http://10.0.0.5/hook",              # RFC1918
        "http://192.168.1.1/hook",           # RFC1918
        "http://169.254.169.254/latest/meta-data",  # cloud metadata
        "http://0.0.0.0/hook",               # unspecified
        "http://internal-api.local/hook",    # mDNS-style internal name
    ):
        r = client.post("/webhooks/subscribe", json={"url": bad})
        assert r.status_code == 400, bad
    assert main.SUBSCRIBED_WEBHOOKS == []


def test_subscribe_private_allowed_with_env_override(monkeypatch):
    monkeypatch.setenv("PRAMAAN_WEBHOOK_ALLOW_PRIVATE", "1")
    r = client.post("/webhooks/subscribe", json={"url": "http://127.0.0.1:9999/hook"})
    assert r.status_code == 200


def test_subscribe_is_idempotent_and_capped(monkeypatch):
    _no_private_override(monkeypatch)
    for _ in range(3):
        client.post("/webhooks/subscribe", json={"url": _PUBLIC_URL})
    assert main.SUBSCRIBED_WEBHOOKS.count(_PUBLIC_URL) == 1

    for i in range(1, main.MAX_WEBHOOKS):
        assert client.post("/webhooks/subscribe",
                           json={"url": f"http://8.8.8.8/hook{i}"}).status_code == 200
    assert len(main.SUBSCRIBED_WEBHOOKS) == main.MAX_WEBHOOKS
    r = client.post("/webhooks/subscribe", json={"url": "http://8.8.8.8/one-too-many"})
    assert r.status_code == 429


# ── list / clear: no secret echo ─────────────────────────────────────

def test_list_redacts_long_urls(monkeypatch):
    _no_private_override(monkeypatch)
    secret_url = "http://8.8.8.8/services/T0000000/B0000000/SECRETSECRETSECRET"
    client.post("/webhooks/subscribe", json={"url": secret_url})
    body = client.get("/webhooks").json()
    assert body["count"] == 1
    assert len(body["urls"]) == 1
    assert "SECRETSECRETSECRET" not in body["urls"][0]
    assert body["urls"][0].startswith("http://8.8.8.8/")


def test_clear_webhooks(monkeypatch):
    _no_private_override(monkeypatch)
    client.post("/webhooks/subscribe", json={"url": _PUBLIC_URL})
    r = client.delete("/webhooks")
    assert r.status_code == 200
    assert r.json() == {"cleared": 1}
    assert client.get("/webhooks").json() == {"count": 0, "urls": []}


# ── trigger: payload routing and defensiveness ───────────────────────

def test_deliver_routes_slack_vs_json(monkeypatch):
    posts = []
    monkeypatch.setattr(
        "httpx.post",
        lambda url, json=None, **kw: posts.append((url, json)),
    )
    payload = {"event": "deviation_detected"}
    slack_payload = {"text": "alert"}
    main._deliver_webhooks(
        ["https://hooks.slack.com/services/T/B/X", "https://example.test/hook"],
        payload, slack_payload,
    )
    assert posts == [
        ("https://hooks.slack.com/services/T/B/X", slack_payload),
        ("https://example.test/hook", payload),
    ]


def test_deliver_survives_a_dead_subscriber(monkeypatch):
    posts = []

    def flaky_post(url, json=None, **kw):
        if "dead" in url:
            raise ConnectionError("refused")
        posts.append(url)

    monkeypatch.setattr("httpx.post", flaky_post)
    main._deliver_webhooks(["https://dead.test/hook", "https://alive.test/hook"],
                           {}, {})
    assert posts == ["https://alive.test/hook"]


def _capture_delivery(monkeypatch):
    """Replace the worker-thread delivery with a synchronous recorder."""
    captured = {}
    done = threading.Event()

    def fake_deliver(urls, payload, slack_payload):
        captured.update(urls=urls, payload=payload, slack_payload=slack_payload)
        done.set()

    monkeypatch.setattr(main, "_deliver_webhooks", fake_deliver)
    return captured, done


def test_trigger_filters_to_critical_and_major(monkeypatch):
    captured, done = _capture_delivery(monkeypatch)
    main.SUBSCRIBED_WEBHOOKS.append(_PUBLIC_URL)
    devs = [
        dict(_DEV, severity="Critical"),
        dict(_DEV, severity="Major", parameter="efficiency_pct"),
        dict(_DEV, severity="Minor", parameter="paint_shade"),
    ]
    main.trigger_webhooks(devs, "UPS")
    assert done.wait(timeout=5)
    assert captured["payload"]["count"] == 2
    params = {d["parameter"] for d in captured["payload"]["deviations"]}
    assert params == {"battery_runtime_min", "efficiency_pct"}
    assert len(captured["payload"]["rfi_drafts"]) == 2
    assert "UPS" in captured["slack_payload"]["text"]


def test_trigger_noop_without_subscribers_or_findings(monkeypatch):
    captured, done = _capture_delivery(monkeypatch)
    main.trigger_webhooks([dict(_DEV)], "UPS")            # no subscribers
    main.SUBSCRIBED_WEBHOOKS.append(_PUBLIC_URL)
    main.trigger_webhooks([dict(_DEV, severity="Minor")], "UPS")  # no Crit/Major
    assert not done.wait(timeout=0.2)
    assert captured == {}


def test_trigger_survives_malformed_deviation_dicts(monkeypatch):
    """LLM output may omit keys — the trigger must not raise into /analyze."""
    captured, done = _capture_delivery(monkeypatch)
    main.SUBSCRIBED_WEBHOOKS.append(_PUBLIC_URL)
    main.trigger_webhooks([{"severity": "Critical"}], "UPS")
    assert done.wait(timeout=5)
    assert captured["payload"]["count"] == 1
    assert "?" in captured["payload"]["rfi_drafts"][0]


def test_analyze_endpoint_fires_webhooks(monkeypatch):
    """End-to-end: a subscribed URL sees the deterministic demo deviations."""
    captured, done = _capture_delivery(monkeypatch)
    main.SUBSCRIBED_WEBHOOKS.append(_PUBLIC_URL)
    spec = "Design Basis: UPS System\nBattery autonomy: 10 min minimum\nEfficiency: 96 %\n"
    sub = "Vendor Submittal: UPS System\nBattery autonomy: 7 min\nEfficiency: 93 %\n"
    r = client.post("/analyze", json={"spec_text": spec, "submittal_text": sub,
                                      "system_id": "UPS"})
    assert r.status_code == 200
    if any(d.get("severity") in ("Critical", "Major") for d in r.json()["deviations"]):
        assert done.wait(timeout=5)
        assert captured["urls"] == [_PUBLIC_URL]
        assert captured["payload"]["system"] == "UPS"


def test_analyze_cache_hit_does_not_refire_webhooks(monkeypatch):
    """A double-click / page refresh replays the cached result — subscribers
    must not receive duplicate alerts for findings already dispatched."""
    calls = []
    monkeypatch.setattr(main, "_deliver_webhooks",
                        lambda urls, payload, slack_payload: calls.append(payload))
    main.SUBSCRIBED_WEBHOOKS.append(_PUBLIC_URL)
    spec = "Design Basis: UPS System\nBattery autonomy: 10 min minimum\n"
    sub = "Vendor Submittal: UPS System\nBattery autonomy: 7 min\n"
    body = {"spec_text": spec, "submittal_text": sub, "system_id": "UPS"}

    r1 = client.post("/analyze", json=body)
    r2 = client.post("/analyze", json=body)
    assert r1.status_code == r2.status_code == 200
    assert r1.json()["cached"] is False
    assert r2.json()["cached"] is True

    deadline = threading.Event()
    deadline.wait(timeout=0.5)  # let any stray daemon thread spawn
    fired = len(calls)
    has_alertable = any(d.get("severity") in ("Critical", "Major")
                        for d in r1.json()["deviations"])
    assert fired == (1 if has_alertable else 0)
