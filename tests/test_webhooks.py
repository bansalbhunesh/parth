"""Case-scoped outbound integrations and SSRF/rebinding defenses."""

import threading

from fastapi.testclient import TestClient

from backend import main

client = TestClient(main.app)
_PUBLIC_URL = "http://8.8.8.8/hook"
_DEV = {
    "component": "UPS-02",
    "parameter": "battery_runtime_min",
    "required_value": "10",
    "provided_value": "7",
    "unit": "min",
    "severity": "Critical",
    "standard_ref": "UPTIME-TIER4",
    "spec_clause": "DB-4.3",
    "predicted_cx_test": "IST-07",
    "lead_time_weeks": 27,
    "rationale": "Battery autonomy below requirement.",
}


def _case(name="Webhook test"):
    created = client.post("/cases", json={"name": name})
    assert created.status_code == 200
    body = created.json()
    return body["case_id"], {"X-Case-Secret": body["secret"]}


def _capture_delivery(monkeypatch):
    captured = {}
    done = threading.Event()

    def fake_deliver(subscriptions, payload, slack_payload):
        captured.update(
            subscriptions=subscriptions,
            payload=payload,
            slack_payload=slack_payload,
        )
        done.set()

    monkeypatch.setattr(main, "_deliver_webhooks", fake_deliver)
    return captured, done


def test_global_webhook_endpoints_are_retired():
    assert client.post("/webhooks/subscribe", json={"url": _PUBLIC_URL}).status_code == 410
    assert client.get("/webhooks").status_code == 410
    assert client.delete("/webhooks").status_code == 410


def test_case_secret_is_required_for_every_integration_operation():
    case_id, headers = _case()
    wrong = {"X-Case-Secret": "wrong"}

    assert client.post(
        f"/cases/{case_id}/webhooks", json={"url": _PUBLIC_URL}
    ).status_code == 404
    assert client.get(f"/cases/{case_id}/webhooks", headers=wrong).status_code == 404
    assert client.delete(f"/cases/{case_id}/webhooks", headers=wrong).status_code == 404
    assert client.get(f"/cases/{case_id}/webhooks", headers=headers).status_code == 200


def test_subscribe_is_case_scoped_idempotent_and_redacted(monkeypatch):
    monkeypatch.delenv("PRAMAAN_WEBHOOK_ALLOW_PRIVATE", raising=False)
    first_id, first_headers = _case("First")
    second_id, second_headers = _case("Second")
    secret_url = "http://8.8.8.8/services/T000/B000/SECRETSECRETSECRET"

    for _ in range(2):
        response = client.post(
            f"/cases/{first_id}/webhooks",
            json={"url": secret_url},
            headers=first_headers,
        )
        assert response.status_code == 200

    first = client.get(f"/cases/{first_id}/webhooks", headers=first_headers).json()
    second = client.get(f"/cases/{second_id}/webhooks", headers=second_headers).json()
    assert first["count"] == 1
    assert "SECRETSECRETSECRET" not in first["urls"][0]
    assert second == {"count": 0, "urls": []}


def test_subscribe_rejects_private_and_non_http_targets(monkeypatch):
    monkeypatch.delenv("PRAMAAN_WEBHOOK_ALLOW_PRIVATE", raising=False)
    case_id, headers = _case()
    bad_urls = (
        "ftp://8.8.8.8/x",
        "file:///etc/passwd",
        "not-a-url",
        "http://127.0.0.1/hook",
        "http://10.0.0.5/hook",
        "http://169.254.169.254/latest/meta-data",
        "http://internal-api.local/hook",
    )
    for url in bad_urls:
        response = client.post(
            f"/cases/{case_id}/webhooks",
            json={"url": url},
            headers=headers,
        )
        assert response.status_code == 400, url


def test_integration_limit_applies_per_case(monkeypatch):
    monkeypatch.delenv("PRAMAAN_WEBHOOK_ALLOW_PRIVATE", raising=False)
    case_id, headers = _case()
    for index in range(main.MAX_WEBHOOKS):
        response = client.post(
            f"/cases/{case_id}/webhooks",
            json={"url": f"http://8.8.8.8/hook-{index}"},
            headers=headers,
        )
        assert response.status_code == 200
    overflow = client.post(
        f"/cases/{case_id}/webhooks",
        json={"url": "http://8.8.8.8/overflow"},
        headers=headers,
    )
    assert overflow.status_code == 429


def test_clear_only_removes_owned_case_integrations(monkeypatch):
    monkeypatch.delenv("PRAMAAN_WEBHOOK_ALLOW_PRIVATE", raising=False)
    case_id, headers = _case()
    client.post(
        f"/cases/{case_id}/webhooks",
        json={"url": _PUBLIC_URL},
        headers=headers,
    )

    response = client.delete(f"/cases/{case_id}/webhooks", headers=headers)

    assert response.json() == {"cleared": 1}
    assert client.get(f"/cases/{case_id}/webhooks", headers=headers).json()["count"] == 0


def test_delivery_routes_payload_and_refuses_redirects(monkeypatch):
    posts = []
    monkeypatch.setattr(
        "httpx.post",
        lambda url, json=None, **kwargs: posts.append((url, json, kwargs)),
    )
    slack = "https://hooks.slack.com/services/T/B/X"
    monkeypatch.setattr(
        main,
        "_resolved_webhook_addresses",
        lambda url: ("8.8.8.8",),
    )
    monkeypatch.setattr(main, "_webhook_url_error", lambda _url: None)
    subscriptions = [
        {"url": slack, "resolved_ips": ("8.8.8.8",)},
        {"url": _PUBLIC_URL, "resolved_ips": ("8.8.8.8",)},
    ]

    main._deliver_webhooks(
        subscriptions,
        {"event": "deviation_detected"},
        {"text": "alert"},
    )

    assert posts[0][1] == {"text": "alert"}
    assert posts[1][1] == {"event": "deviation_detected"}
    assert all(post[2]["follow_redirects"] is False for post in posts)


def test_delivery_drops_dns_rebinding(monkeypatch):
    posts = []
    monkeypatch.setattr("httpx.post", lambda *args, **kwargs: posts.append(args))
    monkeypatch.setattr(main, "_webhook_url_error", lambda _url: None)
    monkeypatch.setattr(
        main,
        "_resolved_webhook_addresses",
        lambda _url: ("10.0.0.8",),
    )

    main._deliver_webhooks(
        [{"url": "https://example.test/hook", "resolved_ips": ("8.8.8.8",)}],
        {},
        {},
    )

    assert posts == []


def test_trigger_requires_case_scope_and_filters_minor_findings(monkeypatch):
    captured, done = _capture_delivery(monkeypatch)
    case_id, _headers = _case()
    main.SUBSCRIBED_WEBHOOKS[case_id] = [
        {"url": _PUBLIC_URL, "resolved_ips": ("8.8.8.8",)}
    ]

    main.trigger_webhooks([_DEV], "UPS")
    assert not done.wait(timeout=0.1)
    main.trigger_webhooks([dict(_DEV, severity="Minor")], "UPS", case_id=case_id)
    assert not done.wait(timeout=0.1)
    main.trigger_webhooks([_DEV], "UPS", case_id=case_id)

    assert done.wait(timeout=2)
    assert captured["payload"]["case_id"] == case_id
    assert captured["payload"]["count"] == 1


def test_adding_case_finding_dispatches_only_to_that_case(monkeypatch):
    captured, done = _capture_delivery(monkeypatch)
    case_id, headers = _case()
    main.SUBSCRIBED_WEBHOOKS[case_id] = [
        {"url": _PUBLIC_URL, "resolved_ips": ("8.8.8.8",)}
    ]

    response = client.post(
        f"/cases/{case_id}/findings",
        json=_DEV,
        headers=headers,
    )

    assert response.status_code == 200
    assert done.wait(timeout=2)
    assert captured["payload"]["case_id"] == case_id
