"""
Extraction Agent — raw document -> structured triples.

Turns an unstructured spec or submittal into machine-readable triples
(component, parameter, value, unit, [clause]).

v2: Added batch extraction, accuracy scoring vs reference, and support for
    both spec and submittal document types.
"""

import json
import pathlib

from backend.llm import complete_json

CORPUS = pathlib.Path(__file__).parent.parent.parent / "data" / "corpus"

EXTRACT_PROMPT = """\
Extract every engineering requirement/value from the document below as triples.
Be thorough — capture ALL numeric values, topology specifications, material
ratings, and completeness requirements mentioned in the document.

=== DOCUMENT ({doc_type}) ===
{text}

Return a JSON array of:
{{
  "component": "<id e.g. UPS-02>",
  "parameter": "<machine_name e.g. battery_runtime_min>",
  "value": <number or string>,
  "unit": "<unit>",
  "clause": "<clause id if present, else null>"
}}
"""


def extract(text: str, doc_type: str = "spec"):
    return complete_json(
        EXTRACT_PROMPT.format(doc_type=doc_type, text=text),
        system="You extract structured engineering data faithfully. "
               "Never invent values not present in the document.",
    )


def extract_all_specs():
    results = []
    specs_dir = CORPUS / "specs"
    if not specs_dir.exists():
        return results
    for f in sorted(specs_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        triples = extract(text, doc_type="spec")
        for t in triples:
            t["system"] = f.stem
            t["source"] = f"specs/{f.name}"
        results.extend(triples)
    return results


def extract_all_submittals():
    results = []
    subs_dir = CORPUS / "submittals"
    if not subs_dir.exists():
        return results
    for f in sorted(subs_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        triples = extract(text, doc_type="submittal")
        for t in triples:
            t["system"] = f.stem
            t["source"] = f"submittals/{f.name}"
        results.extend(triples)
    return results


def score_extraction(extracted, reference_path):
    ref = json.loads((CORPUS / reference_path).read_text())
    ref_keys = {(r["component"], r["parameter"]) for r in ref}
    ext_keys = {(e["component"], e["parameter"]) for e in extracted}

    tp = ref_keys & ext_keys
    fp = ext_keys - ref_keys
    fn = ref_keys - ext_keys

    precision = len(tp) / (len(tp) + len(fp)) if (tp or fp) else 0.0
    recall = len(tp) / (len(tp) + len(fn)) if (tp or fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) else 0.0)

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "tp": len(tp),
        "fp": len(fp),
        "fn": len(fn),
    }
