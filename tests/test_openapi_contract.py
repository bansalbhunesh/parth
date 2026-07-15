"""The reviewed v1 contract is part of the testable repository surface."""

from pathlib import Path

from backend.main import app
from scripts.export_openapi import render_contract


def test_openapi_snapshot_is_current() -> None:
    snapshot = Path(__file__).resolve().parents[1] / "contracts" / "openapi-v1.json"
    assert snapshot.read_text(encoding="utf-8") == render_contract()


def test_contract_rendering_does_not_mutate_the_application_schema() -> None:
    paths_before = set(app.openapi()["paths"])

    render_contract()

    assert set(app.openapi()["paths"]) == paths_before
