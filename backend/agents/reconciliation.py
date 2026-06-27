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
    "the corresponding value in the vendor submittal. The DESIGN BASIS is the "
    "authoritative source of REQUIRED values; use governing standards only to "
    "INTERPRET ambiguous design-basis requirements, never to override them.\n\n"
    "RULES:\n"
    "1. A DEVIATION exists ONLY when the SUBMITTAL value FAILS to meet the "
    "   DESIGN BASIS requirement. If the submittal MATCHES the design-basis "
    "   value, it is COMPLIANT — do NOT flag it, even if you personally believe "
    "   the design basis itself is below a standard. Second-guessing the design "
    "   (when the submittal meets it) is OUT OF SCOPE and a false positive.\n"
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
TASK: Compare the VENDOR SUBMITTAL against the DESIGN BASIS document. Identify
EVERY requirement where the SUBMITTAL FAILS to meet the DESIGN BASIS value. Use
the GOVERNING STANDARDS only to interpret ambiguous design-basis requirements.

STEP-BY-STEP APPROACH:
1. Read the design basis and list each requirement with its required value.
2. For each requirement, find the corresponding value in the submittal.
3. Compare: does the submittal value MEET OR EXCEED the DESIGN-BASIS requirement?
4. If the submittal meets the design basis, it is COMPLIANT — do NOT flag it,
   even if the design-basis value itself looks below a standard. You are
   reviewing the SUBMITTAL against the DESIGN BASIS, not auditing the design.
5. If the submittal falls short of the design basis, classify the deviation
   and assess severity.

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

NAMING DISCIPLINE — use the EXACT identifiers as written in the DESIGN BASIS:
- "component": copy the component id verbatim (e.g. UPS-02, FLOOR, COOL-LOOP).
  Do NOT expand or rename it (not "Raised Floor System" — use "FLOOR").
- "parameter": copy the parameter machine_name verbatim in snake_case
  (e.g. height_mm, delta_t_c, battery_runtime_min). Do NOT paraphrase, expand
  units, or use spaces. Downstream systems match on these exact identifiers.

Return a JSON array of deviations found. Each element:
{{
  "component": "<exact component id, e.g. UPS-02>",
  "parameter": "<exact snake_case machine_name, e.g. battery_runtime_min>",
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


def _standards_text_at(base, max_chars_per=None):
    """Concatenate the governing standards. `max_chars_per` caps each standard
    to its first N chars — the headline thresholds (availability, topology,
    autonomy, ratings) live at the top of each paraphrased summary, so a cap
    keeps what the reconciler needs while cutting prompt tokens (and cost) on
    the high-volume /analyze path. Eval keeps full fidelity (no cap)."""
    parts = []
    for f in sorted((base / "standards").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        if max_chars_per and len(text) > max_chars_per:
            text = (text[:max_chars_per].rstrip()
                    + "\n…[truncated — key requirements above]")
        parts.append(text)
    return "\n\n".join(parts)


def _all_standards_text(max_chars_per=None):
    return _standards_text_at(CORPUS, max_chars_per=max_chars_per)


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


def reconcile_system_at(base, sys_id: str, standards_text: str, with_cx: bool = False):
    """Path-agnostic LLM reconciliation for a single system under `base`
    (a project corpus root with specs/ and submittals/). Set with_cx=True to
    attach commissioning predictions (rule table is Meghdoot-specific)."""
    spec_path = base / "specs" / f"{sys_id}.md"
    sub_path = base / "submittals" / f"{sys_id}.md"
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
        d["system"] = sys_id
        if with_cx:
            d.update(predict_cx_impact(d))
    return devs


def reconcile_system(sys_id: str, standards_text: str):
    return reconcile_system_at(CORPUS, sys_id, standards_text, with_cx=True)


def run_reconciliation_over_corpus():
    standards = _all_standards_text()
    systems = sorted(p.stem for p in (CORPUS / "specs").glob("*.md"))
    findings = []
    for sys_id in systems:
        findings.extend(reconcile_system(sys_id, standards))
    return findings


if __name__ == "__main__":
    print(json.dumps(run_reconciliation_over_corpus(), indent=2))
