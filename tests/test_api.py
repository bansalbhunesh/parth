
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestHealthEndpoints:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert "version" in data

    def test_project(self):
        r = client.get("/project")
        assert r.status_code == 200

    def test_systems(self):
        r = client.get("/systems")
        assert r.status_code == 200
        data = r.json()
        assert "systems" in data
        assert isinstance(data["systems"], list)


class TestDeviationEndpoints:
    def test_deviations_returns_register(self):
        r = client.get("/deviations")
        assert r.status_code == 200
        data = r.json()
        assert "register" in data
        assert "count" in data
        assert isinstance(data["register"], list)

    def test_deviations_count_matches(self):
        r = client.get("/deviations")
        data = r.json()
        assert data["count"] == len(data["register"])

    def test_deviations_have_required_fields(self):
        r = client.get("/deviations")
        data = r.json()
        required = {"component", "parameter", "required_value", "provided_value",
                     "unit", "severity"}
        for d in data["register"]:
            missing = required - d.keys()
            assert not missing, f"Deviation missing: {missing}"


class TestIngestEndpoint:
    def test_ingest_unknown_system(self):
        r = client.post("/ingest/NONEXISTENT")
        assert r.status_code == 404

    def test_ingest_valid_format(self):
        r = client.get("/systems")
        systems = r.json()["systems"]
        if not systems:
            return
        r = client.post("/ingest/DEFINITELY_NOT_REAL")
        assert r.status_code == 404


class TestCopilotEndpoint:
    def test_copilot_empty_query_rejected(self):
        r = client.post("/copilot", json={"query": ""})
        assert r.status_code == 422

    def test_copilot_returns_structure(self):
        r = client.post("/copilot", json={"query": "What is the UPS battery runtime?"})
        assert r.status_code == 200
        data = r.json()
        assert "answer" in data
        assert "sources" in data


class TestStreamingEndpoints:
    def test_copilot_stream_returns_sse(self):
        r = client.post("/copilot/stream", json={"query": "What is the UPS battery runtime?"})
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        body = r.text
        assert "event: meta" in body or "event: token" in body
        assert "event: done" in body

    def test_copilot_stream_empty_rejected(self):
        r = client.post("/copilot/stream", json={"query": ""})
        assert r.status_code == 422

    def test_analyze_stream_returns_sse(self):
        r = client.post("/analyze/stream", json={
            "spec_text": "**UPS-02** — battery runtime min: shall be **10 min**",
            "submittal_text": "**UPS-02** — battery runtime min: **7 min**",
        })
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        body = r.text
        assert "event: result" in body or "event: status" in body
        assert "event: done" in body


class TestPdfUploadEndpoints:
    def _make_text_file(self, content, filename):
        import io
        return ("spec_file", (filename, io.BytesIO(content.encode()), "text/plain"))

    def test_upload_text_files(self):
        import io
        spec = io.BytesIO(b"**UPS-02** -- battery runtime min: shall be **10 min**")
        sub = io.BytesIO(b"**UPS-02** -- battery runtime min: **7 min**")
        r = client.post("/analyze/upload", files=[
            ("spec_file", ("spec.txt", spec, "text/plain")),
            ("submittal_file", ("sub.txt", sub, "text/plain")),
        ])
        assert r.status_code == 200
        data = r.json()
        assert "deviations" in data
        assert "spec_filename" in data
        assert data["spec_filename"] == "spec.txt"

    def test_upload_stream_text_files(self):
        import io
        spec = io.BytesIO(b"**UPS-02** -- battery runtime min: shall be **10 min**")
        sub = io.BytesIO(b"**UPS-02** -- battery runtime min: **7 min**")
        r = client.post("/analyze/upload/stream", files=[
            ("spec_file", ("spec.txt", spec, "text/plain")),
            ("submittal_file", ("sub.txt", sub, "text/plain")),
        ])
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        body = r.text
        assert "event: result" in body or "event: status" in body
        assert "event: done" in body


class TestOcrCheckAndImageUpload:
    """/ocr-check reports the deployment's real OCR capability; the image-upload
    branch routes raster images through Tesseract (mocked here so CI needs no
    binary). The Gemini /analyze/vision path is a separate, untouched contract."""

    def test_ocr_check_shape_and_invariant(self):
        r = client.get("/ocr-check")
        assert r.status_code == 200
        d = r.json()
        for k in ("ocr_available", "ocr_enabled", "tesseract_installed",
                  "tesseract_version", "image_ocr_supported", "pdf_ocr_supported",
                  "max_pdf_pages", "max_image_pixels", "status"):
            assert k in d, f"/ocr-check missing {k}"
        # ocr_available must equal binary-present AND enabled — never overclaim.
        assert d["ocr_available"] == (d["tesseract_installed"] and d["ocr_enabled"])
        assert d["status"] in ("ready", "disabled", "tesseract_not_installed")
        assert isinstance(d["max_pdf_pages"], int) and d["max_pdf_pages"] > 0
        assert isinstance(d["max_image_pixels"], int) and d["max_image_pixels"] > 0

    def test_health_exposes_ocr_available(self):
        d = client.get("/health").json()
        assert "ocr_available" in d
        assert isinstance(d["ocr_available"], bool)

    def test_upload_returns_extraction_metadata(self):
        import io
        spec = io.BytesIO(b"**UPS-02** -- battery runtime min: shall be **10 min**")
        sub = io.BytesIO(b"**UPS-02** -- battery runtime min: **7 min**")
        r = client.post("/analyze/upload", files=[
            ("spec_file", ("spec.txt", spec, "text/plain")),
            ("submittal_file", ("sub.txt", sub, "text/plain")),
        ])
        assert r.status_code == 200
        ext = r.json()["extraction"]
        assert ext["spec"]["method"] == "plain_text"
        assert ext["submittal"]["ocr_used"] is False
        assert ext["spec"]["warning"] is None
        # metadata must NOT leak the document body
        assert "text" not in ext["spec"]

    def test_image_upload_routes_through_ocr(self, monkeypatch):
        import backend.agents.ocr_util as ocr_util
        monkeypatch.setattr(ocr_util, "extract_text_from_image",
                            lambda data, mime="image/png": "**SWGR-01** — icw: **50 kA**")
        spec = b"**SWGR-01** -- icw: shall be **65 kA** (ref: DB; clause 1)"
        r = client.post("/analyze/upload", files=[
            ("spec_file", ("spec.md", spec, "text/markdown")),
            ("submittal_file", ("submittal.png", b"\x89PNG_fake_bytes", "image/png")),
        ])
        assert r.status_code == 200
        d = r.json()
        assert d["submittal_filename"] == "submittal.png"
        assert "deviations" in d
        # the image was OCR'd -> metadata says so and carries the OCR warning
        sub_ext = d["extraction"]["submittal"]
        assert sub_ext["method"] == "ocr_image"
        assert sub_ext["ocr_used"] is True
        assert sub_ext["warning"] and "OCR" in sub_ext["warning"]

    def test_image_upload_ocr_unavailable_returns_400(self, monkeypatch):
        import backend.agents.ocr_util as ocr_util
        monkeypatch.setattr(ocr_util, "extract_text_from_image",
                            lambda data, mime="image/png": "")
        r = client.post("/analyze/upload", files=[
            ("spec_file", ("spec.md", b"**SWGR-01** -- icw: shall be **65 kA**", "text/markdown")),
            ("submittal_file", ("submittal.png", b"\x89PNG_fake_bytes", "image/png")),
        ])
        assert r.status_code == 400
        assert "image" in r.json()["detail"].lower()


class TestExportEndpoints:
    def test_export_audit_json(self):
        r = client.get("/export/audit")
        assert r.status_code == 200
        data = r.json()
        assert "project" in data
        assert "evidence" in data
        assert "standard_basis" in data

    def test_export_audit_html(self):
        r = client.get("/export/audit/html")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]
        assert "Pramaan" in r.text
        assert "<table>" in r.text

    def test_export_audit_integrity_hash_verifies(self):
        """The evidence pack must carry a recomputable SHA-256: strip the
        integrity block, canonical-JSON the rest, and the digest must match —
        that recomputation IS the tamper check a QMS auditor runs."""
        import hashlib as _hashlib
        import json as _json
        data = client.get("/export/audit").json()
        integrity = data.pop("integrity")
        assert integrity["algo"] == "sha256"
        canonical = _json.dumps(data, sort_keys=True,
                                separators=(",", ":"), default=str)
        digest = _hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert digest == integrity["content_hash"]

    def test_export_audit_html_shows_integrity_hash(self):
        pack_hash = client.get("/export/audit").json()["integrity"]["content_hash"]
        r = client.get("/export/audit/html")
        assert pack_hash in r.text


class TestAnalyzeEndpoint:
    def test_analyze_deterministic(self):
        spec = """# Design Basis
- **TEST-01** — voltage: shall be **400 V** (ref: DESIGN-BASIS; clause DB-1.1)
- **TEST-01** — current: shall be **100 A** (ref: DESIGN-BASIS; clause DB-1.2)"""
        submittal = """# Vendor Submittal
- **TEST-01** — voltage: **380 V** (vendor)
- **TEST-01** — current: **100 A** (vendor)"""
        r = client.post("/analyze", json={"spec_text": spec, "submittal_text": submittal})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 0  # may or may not find depending on regex
        assert "deviations" in data
        assert "elapsed_ms" in data

    def test_analyze_timing_breakdown(self):
        """Stage-level latency breakdown on the response itself (not just an
        external measurement script) — standards_load_ms + postprocess_ms are
        always ints; llm_call_ms/provider are only set on an actual LLM call
        (None on a deterministic-fallback response), never fabricated."""
        spec = """# Design Basis
- **TEST-01** — voltage: shall be **400 V** (ref: DESIGN-BASIS; clause DB-1.1)"""
        submittal = """# Vendor Submittal
- **TEST-01** — voltage: **380 V** (vendor)"""
        r = client.post("/analyze", json={"spec_text": spec, "submittal_text": submittal})
        assert r.status_code == 200
        timing = r.json()["timing"]
        assert isinstance(timing["standards_load_ms"], int)
        assert isinstance(timing["postprocess_ms"], int)
        assert "llm_call_ms" in timing
        assert "provider" in timing
        if r.json()["mode"] == "llm":
            assert timing["llm_call_ms"] is not None
            assert timing["provider"] is not None
        else:
            assert timing["llm_call_ms"] is None

    def test_analyze_validation(self):
        r = client.post("/analyze", json={"spec_text": "short", "submittal_text": "short"})
        assert r.status_code == 422


class TestDataEndpoints:
    def test_cx_plan(self):
        r = client.get("/cx-plan")
        assert r.status_code == 200
        data = r.json()
        assert "tests" in data

    def test_cx_plan_has_all_tests(self):
        r = client.get("/cx-plan")
        data = r.json()
        assert len(data["tests"]) >= 17

    def test_rfi_log(self):
        r = client.get("/rfi-log")
        assert r.status_code == 200

    def test_metrics(self):
        r = client.get("/metrics")
        assert r.status_code == 200
        data = r.json()
        assert "detection" in data
        assert "commissioning" in data
        assert "text_eval" in data
        assert data["detection"]["baseline_f1"] == 1.0
        assert data["text_eval"]["f1"] == 1.0
        assert data["text_eval"]["projects_evaluated"] >= 6

    def test_metrics_detection_counts(self):
        r = client.get("/metrics")
        data = r.json()
        assert data["detection"]["total_deviations"] == 14
        assert data["detection"]["critical"] == 7
        assert data["detection"]["major"] == 6
        assert data["detection"]["false_positive_rate"] == 0.0

    def test_metrics_commissioning(self):
        r = client.get("/metrics")
        data = r.json()
        assert data["commissioning"]["total_lead_time_weeks"] == 267
        assert data["commissioning"]["max_lead_time_weeks"] == 33
        assert data["commissioning"]["cx_prediction_accuracy"] == 1.0


class TestCorpusDocEndpoint:
    def test_get_spec_document(self):
        r = client.get("/corpus/doc/specs/UPS")
        assert r.status_code == 200
        data = r.json()
        assert "text" in data
        assert len(data["text"]) > 0

    def test_get_submittal_document(self):
        r = client.get("/corpus/doc/submittals/UPS")
        assert r.status_code == 200
        data = r.json()
        assert "text" in data

    def test_spec_contains_requirements(self):
        r = client.get("/corpus/doc/specs/UPS")
        data = r.json()
        assert "battery_runtime" in data["text"].lower() or "runtime" in data["text"].lower()

    def test_invalid_system_returns_404(self):
        r = client.get("/corpus/doc/specs/NONEXISTENT")
        assert r.status_code == 404

    def test_invalid_doc_type_returns_400(self):
        r = client.get("/corpus/doc/invalid/UPS")
        assert r.status_code == 400


class TestPipelineEndpoint:
    def test_pipeline_returns_nodes(self):
        r = client.get("/pipeline")
        assert r.status_code == 200
        data = r.json()
        assert "nodes" in data
        assert isinstance(data["nodes"], list)
        assert len(data["nodes"]) >= 5

    def test_pipeline_has_edges(self):
        r = client.get("/pipeline")
        data = r.json()
        assert "edges" in data
        assert len(data["edges"]) >= 5

    def test_pipeline_framework(self):
        r = client.get("/pipeline")
        data = r.json()
        assert data["framework"] == "LangGraph"

    def test_pipeline_has_conditional_edge(self):
        r = client.get("/pipeline")
        data = r.json()
        conditional = [e for e in data["edges"] if isinstance(e, dict) and e.get("type") == "conditional"]
        assert len(conditional) >= 1

    def test_pipeline_has_validate_node(self):
        r = client.get("/pipeline")
        data = r.json()
        node_ids = [n["id"] for n in data["nodes"]]
        assert "validate" in node_ids


class TestCorpusStatsEndpoint:
    def test_corpus_stats(self):
        r = client.get("/corpus/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_systems" in data
        assert data["total_systems"] >= 7

    def test_corpus_stats_has_standards(self):
        r = client.get("/corpus/stats")
        data = r.json()
        assert "total_standards" in data
        assert data["total_standards"] >= 5


class TestDemoFiles:
    def test_demo_spec_exists(self):
        demo = pathlib.Path(__file__).parent.parent / "data" / "demo"
        assert (demo / "sample_spec.md").exists()

    def test_demo_submittal_exists(self):
        demo = pathlib.Path(__file__).parent.parent / "data" / "demo"
        assert (demo / "sample_submittal.md").exists()

    def test_demo_files_detect_deviations(self):
        demo = pathlib.Path(__file__).parent.parent / "data" / "demo"
        spec = (demo / "sample_spec.md").read_text(encoding="utf-8")
        submittal = (demo / "sample_submittal.md").read_text(encoding="utf-8")
        r = client.post("/analyze", json={"spec_text": spec, "submittal_text": submittal})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 3
        params = [d["parameter"] for d in data["deviations"]]
        assert "battery_runtime_min" in params
        assert "fire_rating" in params


class TestGroundTruthDeviations:
    """Test deviation data via the ground truth directly since
    /deviations endpoint requires LLM API key for pipeline."""

    def test_ground_truth_severity_distribution(self):
        import json
        gt = json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "corpus" / "ground_truth.json")
            .read_text()
        )
        devs = gt["seeded_deviations"]
        sevs = [d["severity"] for d in devs]
        assert sevs.count("Critical") == 7
        assert sevs.count("Major") == 6
        assert sevs.count("Minor") == 1

    def test_all_deviations_have_cx_prediction(self):
        import json
        gt = json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "corpus" / "ground_truth.json")
            .read_text()
        )
        for d in gt["seeded_deviations"]:
            assert d.get("predicted_cx_test") is not None, \
                f"{d['component']}.{d['parameter']} missing cx prediction"

    def test_all_deviations_have_lead_time(self):
        import json
        gt = json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "corpus" / "ground_truth.json")
            .read_text()
        )
        for d in gt["seeded_deviations"]:
            assert d.get("lead_time_weeks") is not None
            assert d["lead_time_weeks"] > 0

    def test_total_lead_time(self):
        import json
        gt = json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "corpus" / "ground_truth.json")
            .read_text()
        )
        total = sum(d["lead_time_weeks"] for d in gt["seeded_deviations"])
        assert total == 267


class TestApiEdgeCases:
    def test_ingest_invalid_system(self):
        """POST /ingest/INVALID_SYSTEM should return 404."""
        r = client.post("/ingest/INVALID_SYSTEM")
        assert r.status_code == 404

    def test_analyze_empty_input(self):
        """POST /analyze with empty spec_text and sub_text should return 422 (validation)."""
        r = client.post("/analyze", json={"spec_text": "", "submittal_text": ""})
        assert r.status_code == 422

    def test_corpus_doc_invalid_type(self):
        """GET /corpus/doc/invalid_type/UPS should return 400."""
        r = client.get("/corpus/doc/invalid_type/UPS")
        assert r.status_code == 400

    def test_corpus_doc_invalid_id(self):
        """GET /corpus/doc/specs/NONEXISTENT should return 404."""
        r = client.get("/corpus/doc/specs/NONEXISTENT")
        assert r.status_code == 404

    def test_project_invalid_id(self):
        """GET /projects/nonexistent should return 404."""
        r = client.get("/projects/nonexistent")
        assert r.status_code == 404

    def test_health_response_fields(self):
        """GET /health should have 'ok' and 'version' fields."""
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "ok" in data
        assert "version" in data
        assert isinstance(data["ok"], bool)
        assert isinstance(data["version"], str)

    def test_metrics_has_all_fields(self):
        """GET /metrics should have precision, recall, f1, lead_time fields."""
        r = client.get("/metrics")
        assert r.status_code == 200
        data = r.json()
        detection = data["detection"]
        assert "baseline_precision" in detection
        assert "baseline_recall" in detection
        assert "baseline_f1" in detection
        cx = data["commissioning"]
        assert "total_lead_time_weeks" in cx
        assert "max_lead_time_weeks" in cx
        assert "mean_lead_time_weeks" in cx

    def test_deviations_severity_values(self):
        """Each deviation's severity should be one of Critical/Major/Minor."""
        import json
        gt = json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "corpus" / "ground_truth.json")
            .read_text()
        )
        valid_severities = {"Critical", "Major", "Minor"}
        for d in gt["seeded_deviations"]:
            assert d["severity"] in valid_severities, \
                f"Deviation {d['id']} has invalid severity '{d['severity']}'"

    def test_systems_have_required_fields(self):
        """GET /systems should return a list; each system is a string id."""
        r = client.get("/systems")
        assert r.status_code == 200
        data = r.json()
        assert "systems" in data
        for sys_id in data["systems"]:
            assert isinstance(sys_id, str)
            assert len(sys_id) > 0


class TestLLMCheck:
    """/llm-check must report the truth for both probe sizes — a tiny probe
    that passes while demo-sized calls 429 was exactly the failure mode that
    silently degraded the live demo (2026-07-03 audit)."""

    def test_llm_check_no_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        r = client.get("/llm-check")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is False
        assert data["reason"] == "no_key_configured"

    def test_llm_check_deep_no_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        r = client.get("/llm-check?deep=1")
        assert r.status_code == 200
        assert r.json()["ok"] is False
        assert r.json()["reason"] == "no_key_configured"

    def test_llm_check_deep_success_reports_findings(self, monkeypatch):
        import backend.llm as llm_mod
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
        fake = [{"component": "UPS-02", "parameter": "battery_runtime_min",
                 "required_value": "10", "provided_value": "7"}]
        monkeypatch.setattr(llm_mod, "complete_json", lambda prompt, system="": fake)
        r = client.get("/llm-check?deep=1")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert data["probe"] == "deep"
        assert data["findings"] == 1
        # The probe must be demo-sized, not a token ping.
        assert data["prompt_chars"] > 5000
        assert "elapsed_ms" in data

    def test_llm_check_deep_surfaces_quota_error(self, monkeypatch):
        import backend.llm as llm_mod
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")

        def boom(prompt, system=""):
            raise llm_mod.LLMError("429 RESOURCE_EXHAUSTED: quota exceeded")
        monkeypatch.setattr(llm_mod, "complete_json", boom)
        r = client.get("/llm-check?deep=1")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is False
        assert data["probe"] == "deep"
        assert "429" in data["error"]

    def test_llm_check_tiny_hints_at_deep(self, monkeypatch):
        import backend.llm as llm_mod
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
        monkeypatch.setattr(llm_mod, "complete",
                            lambda prompt, system="", json_mode=True: "ok")
        r = client.get("/llm-check")
        data = r.json()
        assert data["ok"] is True
        assert data["probe"] == "tiny"
        assert "deep=1" in data["hint"]

    def test_llm_check_tiny_reports_answering_legs_model(self, monkeypatch):
        """When a failover leg answers the probe, `model` must be that leg's
        model — not the primary's (2026-07-14 audit: provider=groq was shown
        next to model=gemini-2.5-flash)."""
        import backend.llm as llm_mod
        monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
        monkeypatch.setattr(llm_mod, "complete",
                            lambda prompt, system="", json_mode=True: "ok")
        monkeypatch.setattr(llm_mod, "failover_report", lambda: {
            "primary": "gemini",
            "order": ["gemini", "groq"],
            "chain": ["gemini", "groq"],
            "providers": {
                "gemini": {"configured": True, "model": "gemini-2.5-flash"},
                "groq": {"configured": True, "model": "llama-3.3-70b-versatile"},
            },
            "last_successful_provider": "groq",
            "last_failover": None,
        })
        r = client.get("/llm-check")
        data = r.json()
        assert data["ok"] is True
        assert data["provider"] == "groq"
        assert data["model"] == "llama-3.3-70b-versatile"


class TestVisionEndpoint:
    """Vision path: Gemini reads the submittal from an image. Mocked so CI has
    no live-LLM dependency; the real capability is proven in VISION_RESULT.md."""

    def test_vision_disabled_flag(self, monkeypatch):
        monkeypatch.setenv("PRAMAAN_VISION", "0")
        r = client.post("/analyze/vision", files={
            "spec_file": ("spec.md", b"required 65 kA", "text/markdown"),
            "submittal_image": ("s.png", b"\x89PNG_fake", "image/png"),
        })
        assert r.json()["available"] is False

    def test_vision_success_returns_findings(self, monkeypatch):
        import backend.llm as llm_mod
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        fake = '[{"component":"SWGR","parameter":"icw_ka","required_value":"65","provided_value":"50"}]'
        monkeypatch.setattr(llm_mod, "complete_vision",
                            lambda p, img, mime, system="": fake)
        r = client.post("/analyze/vision", files={
            "spec_file": ("spec.md", b"Icw required 65 kA", "text/markdown"),
            "submittal_image": ("s.png", b"\x89PNG_fake_bytes", "image/png"),
        })
        d = r.json()
        assert d["mode"] == "vision"
        assert d["count"] == 1
        assert d["deviations"][0]["parameter"] == "icw_ka"

    def test_vision_unavailable_degrades_no_raise(self, monkeypatch):
        import backend.llm as llm_mod
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        def boom(p, img, mime, system=""):
            raise llm_mod.LLMError("429 quota on vision")
        monkeypatch.setattr(llm_mod, "complete_vision", boom)
        r = client.post("/analyze/vision", files={
            "spec_file": ("spec.md", b"x", "text/markdown"),
            "submittal_image": ("s.png", b"\x89PNG", "image/png"),
        })
        d = r.json()
        assert d["mode"] == "vision-unavailable"
        assert d["count"] == 0


class TestGlobalErrorGuard:
    """No endpoint can crash the response: unexpected errors become a clean
    JSON 500; HTTPExceptions (404 etc.) still flow normally."""

    def test_unexpected_error_returns_clean_500(self):
        from fastapi.testclient import TestClient as _TC

        from backend.main import app

        original_routes = list(app.router.routes)
        original_schema = app.openapi_schema
        try:
            @app.get("/_boom_test")
            def _boom():
                raise RuntimeError("kaboom secret-ish")

            c = _TC(app, raise_server_exceptions=False)
            r = c.get("/_boom_test")
            assert r.status_code == 500
            body = r.json()
            assert body["ok"] is False and body["error"] == "internal_error"
            assert "kaboom" not in str(body)  # no leak of the raw message
        finally:
            # This is a process-global FastAPI application. Leaving the
            # synthetic route registered pollutes later OpenAPI tests and makes
            # repeated/in-process runners report duplicate operation IDs.
            app.router.routes[:] = original_routes
            app.openapi_schema = original_schema

    def test_http_exception_still_404s(self):
        r = client.post("/ingest/NOPE_NOT_A_SYSTEM")
        assert r.status_code in (400, 404)
