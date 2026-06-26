
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

DATA = pathlib.Path(__file__).parent.parent / "data"
CORPUS = DATA / "corpus"
PROJECTS = DATA / "projects"


class TestProjectDiscovery:
    def test_meghdoot_corpus_exists(self):
        assert (CORPUS / "ground_truth.json").exists()

    def test_projects_directory_exists(self):
        assert PROJECTS.exists()

    def test_five_additional_projects(self):
        project_dirs = [p for p in PROJECTS.iterdir() if p.is_dir()]
        assert len(project_dirs) >= 5

    def test_all_projects_have_ground_truth(self):
        for p in PROJECTS.iterdir():
            if p.is_dir():
                assert (p / "ground_truth.json").exists(), f"{p.name} missing ground_truth.json"

    def test_all_projects_have_requirements(self):
        for p in PROJECTS.iterdir():
            if p.is_dir():
                assert (p / "extracted" / "requirements.json").exists(), f"{p.name} missing requirements"

    def test_all_projects_have_submittals(self):
        for p in PROJECTS.iterdir():
            if p.is_dir():
                assert (p / "extracted" / "submittals.json").exists(), f"{p.name} missing submittals"

    def test_all_projects_have_cx_plan(self):
        for p in PROJECTS.iterdir():
            if p.is_dir():
                assert (p / "commissioning" / "cx_plan.json").exists(), f"{p.name} missing cx_plan"

    def test_manifest_exists(self):
        assert (PROJECTS / "manifest.json").exists()


class TestProjectCorpusIntegrity:
    def _project_paths(self):
        return [p for p in PROJECTS.iterdir() if p.is_dir() and (p / "ground_truth.json").exists()]

    def test_ground_truth_has_deviations(self):
        for p in self._project_paths():
            gt = json.loads((p / "ground_truth.json").read_text())
            assert "seeded_deviations" in gt, f"{p.name}: missing seeded_deviations"
            assert len(gt["seeded_deviations"]) > 0, f"{p.name}: no deviations"

    def test_ground_truth_has_project_info(self):
        for p in self._project_paths():
            gt = json.loads((p / "ground_truth.json").read_text())
            proj = gt.get("project", {})
            assert proj.get("name"), f"{p.name}: missing project name"
            assert proj.get("tier"), f"{p.name}: missing tier"
            assert proj.get("location"), f"{p.name}: missing location"

    def test_deviations_have_required_fields(self):
        required = {"id", "system", "component", "parameter", "required_value",
                     "provided_value", "unit", "severity", "predicted_cx_test"}
        for p in self._project_paths():
            gt = json.loads((p / "ground_truth.json").read_text())
            for d in gt["seeded_deviations"]:
                missing = required - d.keys()
                assert not missing, f"{p.name}/{d['id']} missing: {missing}"

    def test_cx_tests_referenced_in_plan(self):
        for p in self._project_paths():
            gt = json.loads((p / "ground_truth.json").read_text())
            plan = json.loads((p / "commissioning" / "cx_plan.json").read_text())
            test_ids = {t["id"] for t in plan["tests"]}
            for d in gt["seeded_deviations"]:
                cx = d.get("predicted_cx_test")
                if cx:
                    assert cx in test_ids, \
                        f"{p.name}/{d['id']}: cx test {cx} not in plan"

    def test_specs_exist_for_deviation_systems(self):
        for p in self._project_paths():
            gt = json.loads((p / "ground_truth.json").read_text())
            specs = {sp.stem for sp in (p / "specs").glob("*.md")} if (p / "specs").exists() else set()
            for d in gt["seeded_deviations"]:
                assert d["system"] in specs, \
                    f"{p.name}/{d['id']}: system {d['system']} has no spec"

    def test_true_negative_systems_have_no_deviations(self):
        for p in self._project_paths():
            gt = json.loads((p / "ground_truth.json").read_text())
            tn = set(gt.get("true_negative_systems", []))
            dev_systems = {d["system"] for d in gt["seeded_deviations"]}
            overlap = tn & dev_systems
            assert not overlap, f"{p.name}: systems in both TN and deviations: {overlap}"


class TestMultiProjectEval:
    def test_eval_discovers_all_projects(self):
        from eval.multi_project_eval import discover_projects
        projects = discover_projects()
        assert "meghdoot" in projects
        assert len(projects) >= 6

    def test_reconcile_each_project(self):
        from eval.multi_project_eval import discover_projects, reconcile_project, load_gt
        for pid, path in discover_projects().items():
            gt_devs, _ = load_gt(path)
            findings = reconcile_project(path)
            assert len(findings) == len(gt_devs), \
                f"{pid}: found {len(findings)} vs {len(gt_devs)} expected"

    def test_all_projects_perfect_f1(self):
        from eval.multi_project_eval import run_all
        results = run_all()
        for pid, r in results.items():
            assert r["scores"]["f1"] == 1.0, f"{pid}: F1={r['scores']['f1']}"

    def test_all_projects_perfect_cx_accuracy(self):
        from eval.multi_project_eval import run_all
        results = run_all()
        for pid, r in results.items():
            assert r["scores"]["cx_prediction_accuracy"] == 1.0, \
                f"{pid}: cx_acc={r['scores']['cx_prediction_accuracy']}"

    def test_all_projects_zero_false_positives(self):
        from eval.multi_project_eval import run_all
        results = run_all()
        for pid, r in results.items():
            assert len(r["scores"]["fp"]) == 0, f"{pid}: has false positives"

    def test_aggregate_metrics(self):
        from eval.multi_project_eval import run_all, aggregate
        results = run_all()
        agg = aggregate(results)
        assert agg["aggregate_f1"] == 1.0
        assert agg["aggregate_precision"] == 1.0
        assert agg["aggregate_recall"] == 1.0
        assert agg["total_deviations"] == 50
        assert agg["total_lead_time_weeks"] > 1000

    def test_project_diversity(self):
        """Verify projects span multiple tiers, countries, and standards."""
        from eval.multi_project_eval import run_all
        results = run_all()
        tiers = {r["tier"] for r in results.values()}
        locations = {r["location"] for r in results.values()}
        assert len(tiers) >= 4, f"Only {len(tiers)} tiers: {tiers}"
        assert len(locations) >= 5, f"Only {len(locations)} locations: {locations}"


class TestLLMDetectorWiring:
    """The multi-project eval exposes a real LLM detector that degrades
    gracefully when no API key is present (the offline/CI path)."""

    def test_llm_detector_runs_without_key(self):
        import os
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        from eval.multi_project_eval import reconcile_project_llm
        # No key -> every system raises LLMError internally -> empty, no crash.
        findings = reconcile_project_llm(CORPUS)
        assert findings == []

    def test_run_all_accepts_llm_detector(self):
        import os
        os.environ.pop("GEMINI_API_KEY", None)
        os.environ.pop("OPENAI_API_KEY", None)
        from eval.multi_project_eval import run_all, aggregate
        # Without a key the LLM detector finds nothing, but the harness still
        # produces a well-formed aggregate (recall 0, no exceptions).
        results = run_all(detector="llm")
        agg = aggregate(results)
        assert agg["projects"] == 12
        assert agg["total_fp"] == 0

    def test_structured_detector_still_default(self):
        from eval.multi_project_eval import run_all, aggregate
        agg = aggregate(run_all())
        assert agg["aggregate_f1"] == 1.0
