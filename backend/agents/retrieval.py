"""Standards retrieval tool — the tool-call behind the retrieval loop.

When a reconciliation finding cites a governing standard that is NOT in the
loaded standards context, the orchestrator calls retrieve_standard() to pull the
most relevant text from the local standards knowledge base (the scraped detailed
standards in data/scraped/), then loops back to re-reason with that context
appended. Deterministic corpus search — no LLM, no network — so the loop is
reproducible and the tool is unit-testable.
"""

import pathlib
import re

_SCRAPED = pathlib.Path(__file__).resolve().parents[2] / "data" / "scraped"
_MAX_CHARS = 1600

# Knowledge base index: canonical key -> (detailed file, alias tokens). Aliases
# are kept specific so a cite for one standard does not pull a sibling (e.g.
# "NFPA 110" must NOT resolve to the NFPA-75 doc).
_INDEX = [
    ("UPTIME-TIER4", "UPTIME-TIER4_detailed.md", ["uptimetier4", "uptimetieriv", "tieriv", "tier4", "uptime"]),
    ("ASHRAE-TC9.9", "ASHRAE-TC9.9_detailed.md", ["ashraetc99", "ashraetc9", "tc99", "ashraethermal"]),
    ("BICSI-002",    "BICSI-002_detailed.md",    ["bicsi002", "bicsi"]),
    ("TIA-942",      "TIA-942_detailed.md",      ["tia942"]),
    ("NFPA-75",      "NFPA-75_detailed.md",      ["nfpa75"]),
    ("IS-1893",      "IS-1893_detailed.md",      ["is1893"]),
]


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", str(s).strip().lower())


def available_standards():
    """The standard keys this tool can retrieve (those with a scraped doc)."""
    return [k for k, fname, _ in _INDEX if (_SCRAPED / fname).exists()]


def retrieve_standard(ref):
    """Return the most relevant standard text for a cited reference, or None if
    the reference is not in the knowledge base."""
    r = _norm(ref)
    if not r:
        return None
    for key, fname, aliases in _INDEX:
        nk = _norm(key)
        if nk in r or r in nk or any(a in r for a in aliases):
            path = _SCRAPED / fname
            if not path.exists():
                return None
            txt = path.read_text(encoding="utf-8").strip()
            if len(txt) > _MAX_CHARS:
                txt = txt[:_MAX_CHARS].rstrip() + "\n…[truncated]"
            return txt
    return None
