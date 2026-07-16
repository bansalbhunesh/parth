"""Cache-aware server-sent events for interactive document analysis."""

from __future__ import annotations

import json
from collections.abc import Iterator

from backend import jobs
from backend.agents.decision import decision_blocks


def cached_analysis_events(
    spec_text: str,
    submittal_text: str,
    system_id: str,
) -> Iterator[str]:
    """Emit progress around the canonical cached analysis path.

    The fixed judge payload shares the same single-flight, cache and provenance
    contract as ``/analyze`` instead of spending provider quota on every click.
    """
    yield "event: status\ndata: Checking the verified analysis cache...\n\n"
    view = jobs.analyze_cached(spec_text, submittal_text, system_id)
    status = (
        "Reused the matching verified analysis result."
        if view["cached"]
        else "Analysis complete; validating decision evidence..."
    )
    yield f"event: status\ndata: {status}\n\n"
    timing = view["timing"]
    result = {
        "system": system_id,
        "request_id": jobs.new_request_id(),
        "input_hash": view["input_hash"],
        "cached": view["cached"],
        "deviations": view["deviations"],
        "count": view["count"],
        **decision_blocks(view["deviations"]),
        "elapsed_ms": view["elapsed_ms"],
        "mode": view["mode"],
        "timing": timing,
        "telemetry": {"total_ms": view["elapsed_ms"], **timing},
    }
    yield f"event: result\ndata: {json.dumps(result)}\n\n"
    yield "event: done\ndata: {}\n\n"
