"""Optional OpenTelemetry bootstrap; safe no-op when export is disabled."""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI

log = logging.getLogger("pramaan.observability")


def configure_observability(app: FastAPI) -> bool:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return False
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": "pramaan-api"}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider, excluded_urls="/health/live")
        return True
    except Exception as exc:  # pragma: no cover - deployment-only integration guard
        log.error("OpenTelemetry initialization failed: %s", str(exc)[:200])
        return False


def current_trace_ids() -> dict[str, Any]:
    try:
        from opentelemetry import trace

        context = trace.get_current_span().get_span_context()
        if context.is_valid:
            return {"trace_id": format(context.trace_id, "032x"), "span_id": format(context.span_id, "016x")}
    except ImportError:
        pass
    return {}
