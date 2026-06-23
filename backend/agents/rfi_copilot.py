"""
RFI / Project Copilot — conversational RAG over the full project corpus.

Answers operational/contractual queries with citations and surfaces prior
similar RFIs to cut re-work.

v2: Improved TF-IDF-style retriever, deviation-aware context, and structured
    response format with prior-RFI matching.
"""

import json
import logging
import math
import pathlib
import re
from collections import Counter

from backend.llm import complete

log = logging.getLogger("pramaan.copilot")

CORPUS = pathlib.Path(__file__).parent.parent.parent / "data" / "corpus"


def _tokenize(text: str):
    return re.findall(r'[a-z0-9]+', text.lower())


def _load_chunks():
    chunks = []
    for sub in ["specs", "submittals", "standards"]:
        d = CORPUS / sub
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            chunks.append({"source": f"{sub}/{f.name}",
                           "text": f.read_text(encoding="utf-8")})

    cx_path = CORPUS / "commissioning" / "cx_plan.json"
    if cx_path.exists():
        cx = json.loads(cx_path.read_text())
        chunks.append({
            "source": "commissioning/cx_plan.json",
            "text": json.dumps(cx, indent=2),
        })

    rfi_path = CORPUS / "rfi" / "rfi_log.json"
    if rfi_path.exists():
        rfis = json.loads(rfi_path.read_text())
        for r in rfis:
            chunks.append({
                "source": f"rfi/{r['id']}",
                "text": f"RFI {r['id']} ({r['system']}, {r['status']}): "
                        f"Q: {r['question']} A: {r.get('resolution') or 'open'}",
                "rfi": r,
            })

    gt_path = CORPUS / "ground_truth.json"
    if gt_path.exists():
        gt = json.loads(gt_path.read_text())
        for d in gt.get("seeded_deviations", []):
            chunks.append({
                "source": f"deviation/{d['id']}",
                "text": (f"Deviation {d['id']}: {d['component']}.{d['parameter']} "
                         f"required={d['required_value']} provided={d['provided_value']} "
                         f"{d['unit']} severity={d['severity']} "
                         f"cx_test={d.get('predicted_cx_test')}"),
            })
    return chunks


def _build_idf(chunks):
    doc_count = len(chunks)
    df = Counter()
    for c in chunks:
        tokens = set(_tokenize(c["text"]))
        for t in tokens:
            df[t] += 1
    return {t: math.log((doc_count + 1) / (freq + 1)) + 1 for t, freq in df.items()}


_CHUNKS = None
_IDF = None


def _ensure_index():
    global _CHUNKS, _IDF
    if _CHUNKS is not None:
        return
    try:
        _CHUNKS = _load_chunks()
        _IDF = _build_idf(_CHUNKS)
    except Exception:
        _CHUNKS = []
        _IDF = {}


def _retrieve(query: str, k: int = 6):
    _ensure_index()
    q_tokens = _tokenize(query)
    if not q_tokens:
        return _CHUNKS[:k]

    q_weights = Counter(q_tokens)
    scored = []
    for c in _CHUNKS:
        c_tokens = Counter(_tokenize(c["text"]))
        score = 0.0
        for t, qf in q_weights.items():
            if t in c_tokens:
                tf = 1 + math.log(c_tokens[t])
                idf = _IDF.get(t, 1.0)
                score += qf * tf * idf
        if score > 0:
            scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:k]]


def ask(query: str):
    log.info("Copilot query: %s", query[:120])
    ctx = _retrieve(query)
    log.info("Retrieved %d context chunks", len(ctx))
    context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in ctx)
    prompt = (
        f"Answer the project question using ONLY the context provided below. "
        f"Cite sources in square brackets like [specs/UPS.md] or [rfi/RFI-014]. "
        f"If a prior RFI is relevant to the question, explicitly mention it and "
        f"quote its resolution. If a known deviation is relevant, mention it.\n\n"
        f"Be specific and technical. Include exact values and clause references.\n\n"
        f"=== CONTEXT ===\n{context}\n\n=== QUESTION ===\n{query}"
    )
    answer = complete(
        prompt,
        system="You are a precise EPC project copilot for a Tier IV data centre. "
               "Cite every claim. Be concise but thorough.",
        json_mode=False,
    )
    prior_rfis = [c["rfi"] for c in ctx if "rfi" in c]
    return {
        "answer": answer,
        "sources": [c["source"] for c in ctx],
        "prior_rfis": prior_rfis,
    }
