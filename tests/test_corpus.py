"""
Tests for corpus integrity — verifies that all required data files exist,
are valid JSON/Markdown, and cross-reference correctly.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

CORPUS = pathlib.Path(__file__).parent.parent / "data" / "corpus"


class TestCorpusStructure:
    def test_corpus_directory_exists(self):
        assert CORPUS.exists()

    def test_ground_truth_exists(self):
        assert (CORPUS / "ground_truth.json").exists()

    def test_ground_truth_valid_json(self):
        gt = json.loads((CORPUS / "ground_truth.json").read_text())
        assert "seeded_deviations" in gt
        assert "project" in gt
        assert "true_negative_systems" in gt

    def test_specs_directory(self):
        specs = CORPUS / "specs"
        assert specs.exists()
        files = list(specs.glob("*.md"))
        assert len(files) >= 7

    def test_submittals_directory(self):
        subs = CORPUS / "submittals"
        assert subs.exists()
        files = list(subs.glob("*.md"))
        assert len(files) >= 7

    def test_standards_directory(self):
        stds = CORPUS / "standards"
        assert stds.exists()
        files = list(stds.glob("*.md"))
        assert len(files) >= 7

    def test_extracted_requirements(self):
        path = CORPUS / "extracted" / "requirements.json"
        assert path.exists()
        reqs = json.loads(path.read_text())
        assert isinstance(reqs, list)
        assert len(reqs) > 0

    def test_extracted_submittals(self):
        path = CORPUS / "extracted" / "submittals.json"
        assert path.exists()
        subs = json.loads(path.read_text())
        assert isinstance(subs, list)
        assert len(subs) > 0

    def test_cx_plan(self):
        path = CORPUS / "commissioning" / "cx_plan.json"
        assert path.exists()
        plan = json.loads(path.read_text())
        assert "tests" in plan
        assert len(plan["tests"]) >= 10

    def test_rfi_log(self):
        path = CORPUS / "rfi" / "rfi_log.json"
        assert path.exists()
        rfis = json.loads(path.read_text())
        assert isinstance(rfis, list)


class TestCrossReferences:
    def test_every_deviation_system_has_spec(self):
        gt = json.loads((CORPUS / "ground_truth.json").read_text())
        specs = {p.stem for p in (CORPUS / "specs").glob("*.md")}
        for d in gt["seeded_deviations"]:
            assert d["system"] in specs, \
                f"Deviation {d['id']} references system {d['system']} with no spec"

    def test_every_deviation_system_has_submittal(self):
        gt = json.loads((CORPUS / "ground_truth.json").read_text())
        subs = {p.stem for p in (CORPUS / "submittals").glob("*.md")}
        for d in gt["seeded_deviations"]:
            assert d["system"] in subs, \
                f"Deviation {d['id']} references system {d['system']} with no submittal"

    def test_cx_test_ids_exist_in_plan(self):
        gt = json.loads((CORPUS / "ground_truth.json").read_text())
        plan = json.loads((CORPUS / "commissioning" / "cx_plan.json").read_text())
        test_ids = {t["id"] for t in plan["tests"]}
        for d in gt["seeded_deviations"]:
            cx = d.get("predicted_cx_test")
            if cx:
                assert cx in test_ids, \
                    f"Deviation {d['id']} references Cx test {cx} not in plan"

    def test_true_negative_systems_have_specs(self):
        gt = json.loads((CORPUS / "ground_truth.json").read_text())
        specs = {p.stem for p in (CORPUS / "specs").glob("*.md")}
        for sys_id in gt["true_negative_systems"]:
            assert sys_id in specs, \
                f"True-negative system {sys_id} has no spec file"

    def test_extracted_requirements_match_specs(self):
        reqs = json.loads((CORPUS / "extracted" / "requirements.json").read_text())
        gt = json.loads((CORPUS / "ground_truth.json").read_text())
        gt_keys = {(d["component"], d["parameter"]) for d in gt["seeded_deviations"]}
        req_keys = {(r["component"], r["parameter"]) for r in reqs}
        for k in gt_keys:
            assert k in req_keys, f"Ground truth deviation {k} not in extracted requirements"


class TestStandardsCorpus:
    def test_standards_not_empty(self):
        for f in (CORPUS / "standards").glob("*.md"):
            text = f.read_text()
            assert len(text) > 100, f"Standard {f.name} suspiciously short ({len(text)} chars)"

    def test_standards_total_lines(self):
        total = 0
        for f in (CORPUS / "standards").glob("*.md"):
            total += f.read_text().count("\n")
        assert total >= 500, f"Standards corpus only {total} lines — expected >=500"
