
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


class TestCorpusIntegrity:
    def test_all_specs_are_valid_markdown(self):
        """All .md files in specs/ should be non-empty and contain headers."""
        specs_dir = CORPUS / "specs"
        files = list(specs_dir.glob("*.md"))
        assert len(files) > 0
        for f in files:
            text = f.read_text()
            assert len(text) > 0, f"Spec {f.name} is empty"
            assert "#" in text, f"Spec {f.name} has no markdown headers"

    def test_all_submittals_reference_system(self):
        """Each submittal filename should match a spec filename."""
        spec_stems = {p.stem for p in (CORPUS / "specs").glob("*.md")}
        sub_stems = {p.stem for p in (CORPUS / "submittals").glob("*.md")}
        for sub in sub_stems:
            assert sub in spec_stems, \
                f"Submittal '{sub}' has no matching spec file"

    def test_standards_are_non_empty(self):
        """All standards .md files should be non-empty."""
        stds_dir = CORPUS / "standards"
        files = list(stds_dir.glob("*.md"))
        assert len(files) > 0
        for f in files:
            text = f.read_text()
            assert len(text.strip()) > 0, f"Standard {f.name} is empty"

    def test_rfi_log_entries_have_required_fields(self):
        """Each RFI should have id, system, subject/question, status."""
        rfis = json.loads((CORPUS / "rfi" / "rfi_log.json").read_text())
        assert len(rfis) > 0
        for rfi in rfis:
            assert "id" in rfi, "RFI missing 'id' field"
            assert "system" in rfi, f"RFI {rfi.get('id')} missing 'system' field"
            assert "question" in rfi or "subject" in rfi, \
                f"RFI {rfi.get('id')} missing 'question'/'subject' field"
            assert "status" in rfi, f"RFI {rfi.get('id')} missing 'status' field"

    def test_ground_truth_deviation_ids_unique(self):
        """No duplicate deviation IDs in ground truth."""
        gt = json.loads((CORPUS / "ground_truth.json").read_text())
        ids = [d["id"] for d in gt["seeded_deviations"]]
        assert len(ids) == len(set(ids)), \
            f"Duplicate deviation IDs found: {[x for x in ids if ids.count(x) > 1]}"

    def test_extracted_requirements_count_matches_specs(self):
        """Number of unique systems in extracted requirements should match spec systems."""
        reqs = json.loads((CORPUS / "extracted" / "requirements.json").read_text())
        spec_systems = {p.stem for p in (CORPUS / "specs").glob("*.md")}
        req_systems = {r["system"] for r in reqs}
        assert req_systems.issubset(spec_systems), \
            f"Extracted requirements reference unknown systems: {req_systems - spec_systems}"
