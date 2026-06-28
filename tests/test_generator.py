
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

ROOT = pathlib.Path(__file__).parent.parent


class TestGeneratorReproducibility:
    """Verify generate_corpus.py produces output matching committed data."""

    def test_generator_produces_14_deviations(self):
        from data.generate_corpus import SYSTEMS
        devs = []
        for sys_id, sys_data in SYSTEMS.items():
            for req in sys_data["requirements"]:
                comp, param, required, *_ = req
                provided = sys_data["submittal"].get(param)
                if provided is not None and str(provided) != str(required):
                    devs.append((comp, param))
        assert len(devs) == 14

    def test_generator_produces_267_weeks(self):
        from data.generate_corpus import DEVIATION_TO_CX, PROJECT, SYSTEMS
        total = 0
        for sys_id, sys_data in SYSTEMS.items():
            for req in sys_data["requirements"]:
                comp, param, required, *_ = req
                provided = sys_data["submittal"].get(param)
                if provided is not None and str(provided) != str(required):
                    cx = DEVIATION_TO_CX.get((comp, param), {})
                    wf = cx.get("week_fail")
                    if wf:
                        total += wf - PROJECT["current_week"]
        assert total == 267

    def test_all_deviations_have_cx_mapping(self):
        from data.generate_corpus import DEVIATION_TO_CX, SYSTEMS
        for sys_id, sys_data in SYSTEMS.items():
            for req in sys_data["requirements"]:
                comp, param, required, *_ = req
                provided = sys_data["submittal"].get(param)
                if provided is not None and str(provided) != str(required):
                    assert (comp, param) in DEVIATION_TO_CX, \
                        f"({comp}, {param}) missing from DEVIATION_TO_CX"

    def test_cx_plan_covers_all_deviation_tests(self):
        from data.generate_corpus import DEVIATION_TO_CX
        cx_plan = json.loads(
            (ROOT / "data" / "corpus" / "commissioning" / "cx_plan.json").read_text()
        )
        plan_ids = {t["id"] for t in cx_plan["tests"]}
        for cx in DEVIATION_TO_CX.values():
            assert cx["cx_test"] in plan_ids, \
                f"Cx test {cx['cx_test']} not in cx_plan"

    def test_generated_content_matches_committed(self):
        from data.generate_corpus import SYSTEMS
        committed = json.loads(
            (ROOT / "data" / "corpus" / "ground_truth.json").read_text()
        )
        committed_set = {
            (d["component"], d["parameter"], str(d["required_value"]), str(d["provided_value"]))
            for d in committed["seeded_deviations"]
        }
        generated_set = set()
        for sys_id, sys_data in SYSTEMS.items():
            for req in sys_data["requirements"]:
                comp, param, required, *_ = req
                provided = sys_data["submittal"].get(param)
                if provided is not None and str(provided) != str(required):
                    generated_set.add((comp, param, str(required), str(provided)))
        assert committed_set == generated_set

    def test_10_systems_defined(self):
        from data.generate_corpus import SYSTEMS
        assert len(SYSTEMS) == 10

    def test_33_requirements_total(self):
        from data.generate_corpus import SYSTEMS
        total = sum(len(s["requirements"]) for s in SYSTEMS.values())
        assert total == 33

    def test_3_true_negative_systems(self):
        from data.generate_corpus import SYSTEMS
        clean = []
        for sys_id, sys_data in SYSTEMS.items():
            has_dev = False
            for req in sys_data["requirements"]:
                comp, param, required, *_ = req
                provided = sys_data["submittal"].get(param)
                if provided is not None and str(provided) != str(required):
                    has_dev = True
                    break
            if not has_dev:
                clean.append(sys_id)
        assert len(clean) == 3
        assert set(clean) == {"FIRE", "BUSWAY", "PDU"}

    def test_7_standards_defined(self):
        from data.generate_corpus import STANDARDS
        assert len(STANDARDS) == 7

    def test_all_systems_have_requirements(self):
        from data.generate_corpus import SYSTEMS
        for sys_id, sys_data in SYSTEMS.items():
            assert len(sys_data["requirements"]) >= 2, \
                f"{sys_id} has fewer than 2 requirements"

    def test_all_systems_have_submittals(self):
        from data.generate_corpus import SYSTEMS
        for sys_id, sys_data in SYSTEMS.items():
            for req in sys_data["requirements"]:
                _, param, *_ = req
                assert param in sys_data["submittal"], \
                    f"{sys_id} missing submittal for {param}"


class TestMultiProjectGenerator:
    """Verify generate_projects.py output matches committed data."""

    def test_11_additional_projects_exist(self):
        projects_dir = ROOT / "data" / "projects"
        project_dirs = [p for p in projects_dir.iterdir()
                        if p.is_dir() and p.name != "__pycache__"]
        assert len(project_dirs) == 11

    def test_manifest_matches_directories(self):
        manifest = json.loads(
            (ROOT / "data" / "projects" / "manifest.json").read_text()
        )
        projects_dir = ROOT / "data" / "projects"
        for pid in manifest["projects"]:
            assert (projects_dir / pid).is_dir(), f"Project {pid} missing"

    def test_all_projects_have_complete_corpus(self):
        projects_dir = ROOT / "data" / "projects"
        required_files = [
            "ground_truth.json",
            "extracted/requirements.json",
            "extracted/submittals.json",
            "commissioning/cx_plan.json",
        ]
        for proj in sorted(projects_dir.iterdir()):
            if not proj.is_dir() or proj.name == "__pycache__":
                continue
            for rf in required_files:
                assert (proj / rf).exists(), \
                    f"{proj.name} missing {rf}"

    def test_aggregate_deviations_equal_50(self):
        meghdoot = json.loads(
            (ROOT / "data" / "corpus" / "ground_truth.json").read_text()
        )
        total = len(meghdoot["seeded_deviations"])
        projects_dir = ROOT / "data" / "projects"
        for proj in sorted(projects_dir.iterdir()):
            gt_path = proj / "ground_truth.json"
            if proj.is_dir() and gt_path.exists():
                gt = json.loads(gt_path.read_text())
                total += len(gt["seeded_deviations"])
        assert total == 50

    def test_aggregate_weeks_equal_1024(self):
        meghdoot = json.loads(
            (ROOT / "data" / "corpus" / "ground_truth.json").read_text()
        )
        total = sum(d["lead_time_weeks"] for d in meghdoot["seeded_deviations"])
        projects_dir = ROOT / "data" / "projects"
        for proj in sorted(projects_dir.iterdir()):
            gt_path = proj / "ground_truth.json"
            if proj.is_dir() and gt_path.exists():
                gt = json.loads(gt_path.read_text())
                total += sum(d["lead_time_weeks"] for d in gt["seeded_deviations"])
        assert total == 1024

    def test_projects_span_11_countries(self):
        all_locations = []
        meghdoot = json.loads(
            (ROOT / "data" / "corpus" / "ground_truth.json").read_text()
        )
        all_locations.append(meghdoot["project"]["location"])
        projects_dir = ROOT / "data" / "projects"
        for proj in sorted(projects_dir.iterdir()):
            gt_path = proj / "ground_truth.json"
            if proj.is_dir() and gt_path.exists():
                gt = json.loads(gt_path.read_text())
                all_locations.append(gt["project"]["location"])
        countries = {loc.split(",")[-1].strip() for loc in all_locations}
        assert len(countries) >= 11
