"""Behavioral tests for the bounded HTTP load-probe helpers."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import load_test_demo as load

ROOT = Path(__file__).resolve().parents[1]


class _Response:
    status_code = 200

    @staticmethod
    def json() -> dict[str, object]:
        return {"mode": "deterministic", "cached": True}


class _AsyncClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    async def get(self, endpoint: str, **_kwargs: object) -> _Response:
        self.calls.append(("GET", endpoint))
        if self.fail:
            raise RuntimeError("connection failed")
        return _Response()

    async def post(self, endpoint: str, **_kwargs: object) -> _Response:
        self.calls.append(("POST", endpoint))
        if self.fail:
            raise RuntimeError("connection failed")
        return _Response()


def _args(**overrides: object) -> SimpleNamespace:
    values = {
        "method": "GET",
        "endpoint": "/health/live",
        "vary": False,
        "concurrency": 2,
        "requests": 2,
        "timeout": 5.0,
        "no_warmup": False,
        "revision": "abc1234",
        "profile_label": "unit-test",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_percentile_and_payload_variation_are_deterministic() -> None:
    assert load._percentile([], 95) == 0.0
    assert load._percentile([30.0, 10.0, 20.0], 50) == 20.0
    assert load._payload(_args(), 3)["submittal_text"] == load._SUB
    assert load._payload(_args(vary=True), 3)["submittal_text"].endswith("(variant 3)")


@pytest.mark.asyncio
async def test_async_probe_dispatches_get_and_post_requests() -> None:
    client = _AsyncClient()
    get_result = await load._one_async(client, _args(), {}, 0)
    post_result = await load._one_async(client, _args(method="POST", endpoint="/analyze"), {}, 1)

    assert client.calls == [("GET", "/health/live"), ("POST", "/analyze")]
    assert get_result[1:] == (200, {"mode": "deterministic", "cached": True})
    assert post_result[1:] == (200, {"mode": "deterministic", "cached": True})


@pytest.mark.asyncio
async def test_async_probe_reports_network_failures_without_crashing() -> None:
    elapsed_ms, status_code, body = await load._one_async(_AsyncClient(fail=True), _args(), {}, 0)

    assert elapsed_ms >= 0
    assert status_code is None
    assert body == {"_error": "connection failed"}


def test_summary_and_evidence_artifact_fail_closed_on_overwrite(tmp_path) -> None:
    args = _args(method="POST", endpoint="/analyze", requests=3)
    summary = load._summarize(
        [
            (10.0, 200, {"cached": True, "mode": "deterministic"}),
            (15.0, 302, {}),
            (20.0, 429, {}),
        ],
        0.1,
        args,
    )
    output = tmp_path / "load-evidence.json"

    load._write_evidence(output, "http://service.test", args, summary)
    artifact = json.loads(output.read_text(encoding="utf-8"))

    assert artifact["schema_version"] == 1
    assert artifact["profile"]["label"] == "unit-test"
    assert artifact["profile"]["revision"] == "abc1234"
    assert artifact["profile"]["target"] == "http://service.test"
    assert artifact["results"]["success_rate_percent"] == 33.333
    assert artifact["results"]["rate_limited_429"] == 1
    assert artifact["results"]["errors"] == 1
    assert artifact["results"]["cache_hits"] == 1
    assert artifact["results"]["analysis_modes"] == {"deterministic": 1}
    with pytest.raises(FileExistsError):
        load._write_evidence(output, "http://service.test", args, summary)


def test_committed_load_evidence_is_complete_and_secret_free() -> None:
    artifacts = sorted((ROOT / "docs" / "evidence" / "load").glob("*.json"))
    assert len(artifacts) >= 4

    for path in artifacts:
        text = path.read_text(encoding="utf-8")
        artifact = json.loads(text)
        profile = artifact["profile"]
        results = artifact["results"]

        assert artifact["schema_version"] == 1
        assert profile["revision"] and profile["label"] and profile["target"]
        assert results["requests_attempted"] == profile["requests"]
        assert results["success_2xx"] + results["rate_limited_429"] + results["errors"] == results["requests_attempted"]
        assert set(results["latency_ms"]) == {"p50", "p95", "min", "max"}
        assert artifact["limitations"]
        assert "x-demo-token" not in text.lower()
        assert "authorization" not in text.lower()
