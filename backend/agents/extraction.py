"""
Extraction Agent — raw document -> structured triples.

Turns an unstructured spec or submittal into machine-readable triples
(component, parameter, value, unit, [clause]). Gemini multimodal handles tables
and drawings in production; here we prompt over text. Extraction accuracy is the
foundation of detection quality — invest here first.
"""

from backend.llm import complete_json

EXTRACT_PROMPT = """\
Extract every engineering requirement/value from the document below as triples.

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
