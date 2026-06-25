"""
Reconciliation / Deviation Agent — cross-document reasoning across design
basis, vendor submittal, and governing standards.
"""

import json
import logging

from backend.llm import complete_json, LLMError
from backend.agents.commissioning import predict_cx_impact
from backend.paths import CORPUS

log = logging.getLogger("pramaan.reconciliation")

SYSTEM_PROMPT = (
    "You are a senior data-centre commissioning authority (CxA) with 20+ years "
    "of experience reviewing EPC submittals for hyperscale facilities against "
    "design-basis documents and governing standards (Uptime Tier IV, TIA-942, "
    "BICSI-002, NFPA 75, IS 1893). You find specification deviations that "
    "humans miss because the spec, the submittal, and the standard live in "
    "three different documents and are often written by three different parties.\n\n"
    "Your task: CROSS-REFERENCE each requirement in the design basis against "
    "the corresponding value in the vendor submittal. Apply the governing "
    "standard as the authoritative interpretation when there is ambiguity.\n\n"
    "RULES:\n"
    "1. A DEVIATION exists when the submittal value FAILS to meet the design "
    "   basis requirement OR violates a governing standard.\n"
    "2. NUMERIC thresholds: if the spec says 'shall be X' and the submittal "
    "   provides a value LESS than X (for minimums) or MORE than X (for maximums), "
    "   that is a deviation. Example: spec says '10 min' and submittal says '7 min' "
    "   -> deviation.\n"
    "3. REDUNDANCY levels: N+2 > N+1 > N. If the spec requires N+2 and the "
    "   submittal provides N+1, that is a deviation — N+1 does not satisfy N+2.\n"
    "4. FIRE RATINGS: CMP (plenum) > CMR (riser) > CM (general). If the spec "
    "   requires CMP and the submittal provides CMR, that is a deviation.\n"
    "5. OMISSIONS: if the spec requires 'complete' coverage of something and the "
    "   submittal explicitly states something is missing/pending/not included, "
    "   that is a deviation.\n"
    "6. Values that are EQUIVALENT or EXCEED the requirement are NOT deviations.\n"
    "7. Format or style differences (e.g. '2N' vs 'two-N') are NOT deviations.\n"
    "8. Never invent clauses — cite exact spec_clause and standard_ref from "
    "   the documents.\n"
    "9. Be thorough: check EVERY requirement row, not just obvious ones.\n"
    "10. Do NOT report false positives — only genuine non-conformances."
)

PROMPT_TEMPLATE = """\
TASK: Compare the VENDOR SUBMITTAL against the DESIGN BASIS document, using the
GOVERNING STANDARDS as authoritative interpretation. Identify EVERY requirement
where the submittal FAILS to meet the design basis or a governing standard.

STEP-BY-STEP APPROACH:
1. Read the design basis and list each requirement with its required value.
2. For each requirement, find the corresponding value in the submittal.
3. Compare: does the submittal value MEET OR EXCEED the requirement?
4. If not, classify the deviation and assess severity.
5. Cross-check against the governing standards for additional context.

IMPORTANT — pay attention to:
- Numeric values below specified minimums (e.g. 7 < 10, 12 < 24, 40 < 50)
- Redundancy topology shortfalls (e.g. N+1 when N+2 is required)
- Material/rating downgrades (e.g. CMR when CMP is required)
- Missing/omitted items when completeness is required
- Values that are "close but not quite" — these are the ones humans miss

=== DESIGN BASIS (spec) ===
{spec}

=== VENDOR SUBMITTAL ===
{submittal}

=== GOVERNING STANDARDS (paraphrased) ===
{standards}

Return a JSON array of deviations found. Each element:
{{
  "component": "<e.g. UPS-02>",
  "parameter": "<machine_name e.g. battery_runtime_min>",
  "required_value": <value from design basis — number or string>,
  "provided_value": <value from submittal — number or string>,
  "unit": "<unit>",
  "standard_ref": "<e.g. UPTIME-TIER4>",
  "spec_clause": "<e.g. DB-4.3>",
  "severity": "Critical|Major|Minor",
  "rationale": "<one sentence: why this violates the requirement, referencing the standard>",
  "confidence": <0.0 to 1.0 — your confidence this is a genuine deviation>
}}

If there are ZERO deviations for this system, return an empty array [].
Do NOT include items that meet or exceed their requirements.
"""


def _read(p):
    return (CORPUS / p).read_text(encoding="utf-8")


def _all_standards_text():
    parts = []
    for f in sorted((CORPUS / "standards").glob("*.md")):
        parts.append(f.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def _check_citation_faithfulness(devs, spec_text, submittal_text, standards_text):
    all_text = (spec_text + submittal_text + standards_text).lower()
    for d in devs:
        clause = str(d.get("spec_clause", "")).strip().lower()
        std = str(d.get("standard_ref", "")).strip().lower()
        clause_found = bool(clause) and (clause in all_text or clause.replace("-", "") in all_text)
        std_found = bool(std) and (std in all_text or std.replace("-", "") in all_text)
        d["citation_faithful"] = clause_found and std_found
    return devs


REQUIRED_DEV_KEYS = {"component", "parameter", "required_value", "provided_value"}


def _validate_deviations(raw) -> list[dict]:
    if isinstance(raw, dict):
        raw = raw.get("deviations", [])
    if not isinstance(raw, list):
        log.warning("LLM returned non-list type: %s", type(raw).__name__)
        return []
    valid = []
    for i, d in enumerate(raw):
        if not isinstance(d, dict):
            log.warning("Skipping non-dict deviation at index %d", i)
            continue
        missing = REQUIRED_DEV_KEYS - d.keys()
        if missing:
            log.warning("Deviation %d missing keys %s, skipping", i, missing)
            continue
        d.setdefault("unit", "")
        d.setdefault("severity", "Major")
        d.setdefault("standard_ref", "DESIGN-BASIS")
        d.setdefault("spec_clause", "")
        d.setdefault("rationale", "")
        d.setdefault("confidence", 0.5)
        valid.append(d)
    return valid


def reconcile_system(sys_id: str, standards_text: str):
    spec_path = CORPUS / "specs" / f"{sys_id}.md"
    sub_path = CORPUS / "submittals" / f"{sys_id}.md"
    if not spec_path.exists() or not sub_path.exists():
        log.warning("Missing spec or submittal for %s", sys_id)
        return []
    spec = spec_path.read_text(encoding="utf-8")
    submittal = sub_path.read_text(encoding="utf-8")
    prompt = PROMPT_TEMPLATE.format(
        spec=spec, submittal=submittal, standards=standards_text
    )
    try:
        raw = complete_json(prompt, system=SYSTEM_PROMPT)
    except LLMError as exc:
        log.error("LLM reconciliation failed for %s: %s", sys_id, exc)
        return []
    devs = _validate_deviations(raw)
    devs = _check_citation_faithfulness(devs, spec, submittal, standards_text)
    log.info("System %s: %d deviations found", sys_id, len(devs))
    for d in devs:
        d.update(predict_cx_impact(d))
    return devs


def run_reconciliation_over_corpus():
    standards = _all_standards_text()
    systems = sorted(p.stem for p in (CORPUS / "specs").glob("*.md"))
    findings = []
    for sys_id in systems:
        findings.extend(reconcile_system(sys_id, standards))
    return findings


if __name__ == "__main__":
    print(json.dumps(run_reconciliation_over_corpus(), indent=2))
