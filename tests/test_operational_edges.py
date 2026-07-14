"""Operational edge coverage for extraction and telemetry boundaries."""

from __future__ import annotations

import json
import sys
from types import ModuleType, SimpleNamespace

import pytest
from fastapi import FastAPI

from backend.agents import extraction
from backend.platform import observability


def test_extract_preserves_document_type_and_non_invention_instruction(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        extraction,
        "complete_json",
        lambda prompt, system: calls.append((prompt, system)) or [{"component": "UPS-1"}],
    )

    assert extraction.extract("runtime shall be 10 minutes", "submittal") == [{"component": "UPS-1"}]
    assert "DOCUMENT (submittal)" in calls[0][0]
    assert "runtime shall be 10 minutes" in calls[0][0]
    assert "Never invent values" in calls[0][1]


def test_bulk_extraction_handles_missing_corpus_directories(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(extraction, "CORPUS", tmp_path)
    assert extraction.extract_all_specs() == []
    assert extraction.extract_all_submittals() == []


def test_bulk_extraction_is_sorted_and_adds_source_provenance(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    specs = tmp_path / "specs"
    submittals = tmp_path / "submittals"
    specs.mkdir()
    submittals.mkdir()
    (specs / "B.md").write_text("spec-b", encoding="utf-8")
    (specs / "A.md").write_text("spec-a", encoding="utf-8")
    (submittals / "B.md").write_text("sub-b", encoding="utf-8")
    (submittals / "A.md").write_text("sub-a", encoding="utf-8")
    monkeypatch.setattr(extraction, "CORPUS", tmp_path)
    monkeypatch.setattr(
        extraction,
        "extract",
        lambda text, doc_type: [{"component": text, "parameter": doc_type}],
    )

    spec_results = extraction.extract_all_specs()
    submittal_results = extraction.extract_all_submittals()

    assert [item["system"] for item in spec_results] == ["A", "B"]
    assert [item["source"] for item in spec_results] == ["specs/A.md", "specs/B.md"]
    assert [item["parameter"] for item in spec_results] == ["spec", "spec"]
    assert [item["system"] for item in submittal_results] == ["A", "B"]
    assert [item["source"] for item in submittal_results] == ["submittals/A.md", "submittals/B.md"]
    assert [item["parameter"] for item in submittal_results] == ["submittal", "submittal"]


def test_extraction_scoring_covers_empty_and_mixed_confusion_sets(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    reference = tmp_path / "reference.json"
    reference.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(extraction, "CORPUS", tmp_path)
    assert extraction.score_extraction([], "reference.json") == {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "tp": 0,
        "fp": 0,
        "fn": 0,
    }

    reference.write_text(
        json.dumps(
            [
                {"component": "A", "parameter": "runtime"},
                {"component": "B", "parameter": "rating"},
            ]
        ),
        encoding="utf-8",
    )
    score = extraction.score_extraction(
        [
            {"component": "A", "parameter": "runtime"},
            {"component": "C", "parameter": "material"},
        ],
        "reference.json",
    )
    assert score == {"precision": 0.5, "recall": 0.5, "f1": 0.5, "tp": 1, "fp": 1, "fn": 1}


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
