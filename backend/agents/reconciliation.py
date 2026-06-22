"""
Reconciliation / Deviation Agent — the brain.

Given the RAW spec doc, the RAW submittal doc, and the relevant standard
summaries, it reasons across all three and returns structured deviations with a
citation chain. This is the part no commercial EPC tool does: cross-document
reasoning that ties a procurement value to a standard requirement.

run_reconciliation_over_corpus() is the drop-in the eval harness calls with
--detector llm. It recovers deviations from UNSTRUCTURED text (the hard task the
deterministic baseline cannot do).
"""

import pathlib

from backend.llm import complete_json
from backend.agents.commissioning import predict_cx_impact

CORPUS = pathlib.Path(__file__).parent.parent.parent / "data" / "corpus"

SYSTEM_PROMPT = (
    "You are a senior data-centre commissioning authority reviewing an EPC "
    "submittal against the owner's Design Basis and the governing standards "
    "(Uptime Tier IV, TIA-942, BICSI-002, NFPA 75). You find specification "
    "deviations that humans miss because the spec, the submittal, and the "
    "standard live in three different documents. You never invent clauses; "
    "every finding must cite the exact spec clause and standard it relies on. "
    "You report ONLY genuine non-conformances, not stylistic differences."
)

PROMPT_TEMPLATE = """\
Compare the SUBMITTAL against the DESIGN BASIS and the STANDARDS. Identify every
requirement where the submittal FAILS to meet the design basis or a governing
standard. A value that is merely formatted differently but equivalent is NOT a
deviation. Subtle shortfalls (e.g. a runtime, autonomy, rating, redundancy level
or fire class below what is required) ARE deviations.

=== DESIGN BASIS (spec) ===
{spec}

=== VENDOR SUBMITTAL ===
{submittal}

=== GOVERNING STANDARDS (paraphrased) ===
{standards}

Return a JSON array. Each element:
{{
  "component": "<e.g. UPS-02>",
  "parameter": "<machine_name e.g. battery_runtime_min>",
  "required_value": <value from design basis>,
  "provided_value": <value from submittal>,
  "unit": "<unit>",
  "standard_ref": "<e.g. UPTIME-TIER4>",
  "spec_clause": "<e.g. DB-4.3>",
  "severity": "Critical|Major|Minor",
  "rationale": "<one sentence: why this violates the requirement>"
}}
If there are no deviations, return [].
"""


def _read(p):
    return (CORPUS / p).read_text(encoding="utf-8")


def reconcile_system(sys_id: str, standards_text: str):
    spec = _read(f"specs/{sys_id}.md")
    submittal = _read(f"submittals/{sys_id}.md")
    prompt = PROMPT_TEMPLATE.format(
        spec=spec, submittal=submittal, standards=standards_text
    )
    devs = complete_json(prompt, system=SYSTEM_PROMPT)
    if isinstance(devs, dict):
        devs = devs.get("deviations", [])
    # enrich every deviation with the commissioning-impact prediction
    for d in devs:
        d.update(predict_cx_impact(d))
    return devs


def _all_standards_text():
    parts = []
    for f in sorted((CORPUS / "standards").glob("*.md")):
        parts.append(f.read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def run_reconciliation_over_corpus():
    """Drop-in for the eval harness (--detector llm)."""
    standards = _all_standards_text()
    systems = sorted(p.stem for p in (CORPUS / "specs").glob("*.md"))
    findings = []
    for sys_id in systems:
        findings.extend(reconcile_system(sys_id, standards))
    return findings


if __name__ == "__main__":
    import json
    print(json.dumps(run_reconciliation_over_corpus(), indent=2))
