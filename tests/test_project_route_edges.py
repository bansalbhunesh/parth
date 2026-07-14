"""Graceful-degradation contracts for every project capability route."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.routers import projects


@pytest.fixture(autouse=True)
def _clear_ps4_cache():
    projects._PS4_CACHE.clear()
    yield
    projects._PS4_CACHE.clear()


def test_corpus_stats_and_project_listing_handle_absent_optional_directories(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(projects, "CORPUS", tmp_path)
    monkeypatch.setattr(projects, "PROJECTS_DIR", tmp_path / "projects-missing")
    monkeypatch.setattr(projects, "ingest_corpus", lambda: {"systems": [], "standards": []})
    monkeypatch.setattr(projects, "_load_json", lambda _name: None)

    assert projects.corpus_stats() == {
        "total_systems": 0,
        "total_standards": 0,
        "total_documents": 0,
        "standards_lines": 0,
    }
    assert projects.list_projects() == {"projects": [], "count": 0}


def test_project_listing_skips_files_and_directories_without_ground_truth(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "projects"
    project_root.mkdir()
    (project_root / "plain-file").write_text("not a project", encoding="utf-8")
    (project_root / "missing-ground-truth").mkdir()
    monkeypatch.setattr(projects, "PROJECTS_DIR", project_root)
    monkeypatch.setattr(projects, "_load_json", lambda _name: None)
    assert projects.list_projects() == {"projects": [], "count": 0}


def test_project_loader_rejects_malformed_json(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = tmp_path / "projects"
    bad = project_root / "bad"
    bad.mkdir(parents=True)
    (bad / "schedule.json").write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(projects, "PROJECTS_DIR", project_root)
    assert projects._load_project_file("bad", "schedule.json") is None


def test_schedule_cache_is_reused_and_failures_are_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    cached = {"available": True, "source": "cache"}
    projects._PS4_CACHE[("schedule", "cached")] = cached
    assert projects.project_schedule("cached") is cached

    projects._PS4_CACHE.clear()
    monkeypatch.setattr(
        projects,
        "_load_project_file",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("schedule backend failed")),
    )
    result = projects.project_schedule("broken")
    assert result == {"available": False, "error": "schedule backend failed"}


def test_supply_chain_missing_data_and_failure_are_distinguishable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(projects, "_load_project_file", lambda *_args: None)
    assert projects.project_supply_chain("missing") == {"available": False}

    monkeypatch.setattr(
        projects,
        "_load_project_file",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("supplier backend failed")),
    )
    assert projects.project_supply_chain("broken") == {
        "available": False,
        "error": "supplier backend failed",
    }


def test_graph_assembly_and_view_handle_missing_and_failed_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(projects, "_load_project_file", lambda *_args: None)
    assert projects._assemble_project_graph("missing") == (None, None)

    monkeypatch.setattr(projects, "_assemble_project_graph", lambda _project: (None, None))
    assert projects.project_graph_view("missing") == {"available": False}

    monkeypatch.setattr(
        projects,
        "_assemble_project_graph",
        lambda _project: (_ for _ in ()).throw(RuntimeError("graph backend failed")),
    )
    assert projects.project_graph_view("broken") == {
        "available": False,
        "error": "graph backend failed",
    }


def test_blast_radius_covers_flag_missing_graph_and_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAMAAN_GRAPH", "0")
    assert projects.project_blast_radius("p", "D-1") == {"available": False}

    monkeypatch.setenv("PRAMAAN_GRAPH", "1")
    monkeypatch.setattr(projects, "_assemble_project_graph", lambda _project: (None, None))
    assert projects.project_blast_radius("p", "D-1") == {"available": False}

    monkeypatch.setattr(
        projects,
        "_assemble_project_graph",
        lambda _project: (_ for _ in ()).throw(RuntimeError("blast backend failed")),
    )
    assert projects.project_blast_radius("p", "D-1") == {
        "available": False,
        "error": "blast backend failed",
    }


def test_remediation_route_covers_every_graceful_degradation_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PRAMAAN_GRAPH", "0")
    assert projects.project_remediation("p", "D-1") == {"available": False}

    monkeypatch.setenv("PRAMAAN_GRAPH", "1")
    monkeypatch.setattr(projects, "_assemble_project_graph", lambda _project: (None, None))
    assert projects.project_remediation("p", "D-1") == {"available": False}

    graph = object()
    pg = SimpleNamespace(simulate_remediation=lambda *_args, **_kwargs: None)
    monkeypatch.setattr(projects, "_assemble_project_graph", lambda _project: (pg, graph))
    assert projects.project_remediation("p", "D-1") == {"available": False}

    pg = SimpleNamespace(
        simulate_remediation=lambda *_args, **kwargs: {
            "deviation": "D-1",
            "cost_per_week_lakh": kwargs["cost_per_week_lakh"],
        }
    )
    monkeypatch.setattr(projects, "_assemble_project_graph", lambda _project: (pg, graph))
    assert projects.project_remediation("p", "D-1", 125.0) == {
        "available": True,
        "deviation": "D-1",
        "cost_per_week_lakh": 125.0,
    }

    monkeypatch.setattr(
        projects,
        "_assemble_project_graph",
        lambda _project: (_ for _ in ()).throw(RuntimeError("remediation backend failed")),
    )
    assert projects.project_remediation("p", "D-1") == {
        "available": False,
        "error": "remediation backend failed",
    }


def test_aggregate_route_redacts_internal_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        projects,
        "_compute_projects_aggregate",
        lambda: (_ for _ in ()).throw(RuntimeError("database password must not leak")),
    )
    assert projects.projects_eval_aggregate() == {
        "aggregate": {},
        "per_project": {},
        "error": "aggregate temporarily unavailable",
    }
