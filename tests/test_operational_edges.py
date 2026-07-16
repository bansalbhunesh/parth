"""Operational edge coverage for telemetry boundaries."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest
from fastapi import FastAPI

from backend.platform import observability


def test_observability_is_a_noop_without_export_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    assert observability.configure_observability(FastAPI()) is False


def test_observability_configures_correlated_otlp_export(monkeypatch: pytest.MonkeyPatch) -> None:
    from opentelemetry import trace

    calls: dict[str, object] = {}

    class Provider:
        def __init__(self, *, resource) -> None:  # noqa: ANN001
            calls["resource"] = resource

        def add_span_processor(self, processor) -> None:  # noqa: ANN001
            calls["processor"] = processor

    resource_module = ModuleType("opentelemetry.sdk.resources")
    resource_module.Resource = SimpleNamespace(create=lambda attrs: ("resource", attrs))
    trace_exporter_module = ModuleType("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    trace_exporter_module.OTLPSpanExporter = lambda *, endpoint: ("exporter", endpoint)
    sdk_trace_module = ModuleType("opentelemetry.sdk.trace")
    sdk_trace_module.TracerProvider = Provider
    sdk_export_module = ModuleType("opentelemetry.sdk.trace.export")
    sdk_export_module.BatchSpanProcessor = lambda exporter: ("processor", exporter)
    instrumentation_module = ModuleType("opentelemetry.instrumentation.fastapi")
    instrumentation_module.FastAPIInstrumentor = SimpleNamespace(
        instrument_app=lambda app, **kwargs: calls.update(app=app, instrument=kwargs)
    )
    for name, module in {
        "opentelemetry.exporter": ModuleType("opentelemetry.exporter"),
        "opentelemetry.exporter.otlp": ModuleType("opentelemetry.exporter.otlp"),
        "opentelemetry.exporter.otlp.proto": ModuleType("opentelemetry.exporter.otlp.proto"),
        "opentelemetry.exporter.otlp.proto.http": ModuleType("opentelemetry.exporter.otlp.proto.http"),
        "opentelemetry.exporter.otlp.proto.http.trace_exporter": trace_exporter_module,
        "opentelemetry.instrumentation": ModuleType("opentelemetry.instrumentation"),
        "opentelemetry.instrumentation.fastapi": instrumentation_module,
        "opentelemetry.sdk": ModuleType("opentelemetry.sdk"),
        "opentelemetry.sdk.resources": resource_module,
        "opentelemetry.sdk.trace": sdk_trace_module,
        "opentelemetry.sdk.trace.export": sdk_export_module,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://otel.example/")
    monkeypatch.setattr(trace, "set_tracer_provider", lambda provider: calls.update(trace_provider=provider))
    app = FastAPI()

    assert observability.configure_observability(app) is True
    assert calls["resource"] == ("resource", {"service.name": "pramaan-api"})
    assert calls["processor"] == ("processor", ("exporter", "https://otel.example/v1/traces"))
    assert calls["app"] is app
    assert calls["instrument"] == {"tracer_provider": calls["trace_provider"], "excluded_urls": "/health/live"}


def test_current_trace_ids_returns_only_valid_correlated_context(monkeypatch: pytest.MonkeyPatch) -> None:
    from opentelemetry import trace

    valid = SimpleNamespace(is_valid=True, trace_id=0xABC, span_id=0x123)
    monkeypatch.setattr(trace, "get_current_span", lambda: SimpleNamespace(get_span_context=lambda: valid))
    assert observability.current_trace_ids() == {
        "trace_id": "00000000000000000000000000000abc",
        "span_id": "0000000000000123",
    }

    invalid = SimpleNamespace(is_valid=False, trace_id=0, span_id=0)
    monkeypatch.setattr(trace, "get_current_span", lambda: SimpleNamespace(get_span_context=lambda: invalid))
    assert observability.current_trace_ids() == {}
