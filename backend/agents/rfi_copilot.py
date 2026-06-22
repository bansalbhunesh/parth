"""
RFI / Project Copilot — conversational RAG over the full project corpus.

Answers operational/contractual queries with citations and surfaces prior
similar RFIs to cut re-work. Uses a lightweight in-memory retriever so the repo
runs with zero external vector DB; swap _retrieve() for pgvector/Qdrant at scale.
"""

import json
import pathlib

from backend.llm import complete

CORPUS = pathlib.Path(__file__).parent.parent.parent / "data" / "corpus"


def _load_chunks():
    chunks = []
    for sub in ["specs", "submittals", "standards"]:
        for f in sorted((CORPUS / sub).glob("*.md")):
            chunks.append({"source": f"{sub}/{f.name}",
                           "text": f.read_text(encoding="utf-8")})
    rfis = json.loads((CORPUS / "rfi" / "rfi_log.json").read_text())
    for r in rfis:
        chunks.append({
            "source": f"rfi/{r['id']}",
            "text": f"RFI {r['id']} ({r['system']}, {r['status']}): "
                    f"Q: {r['question']} A: {r.get('resolution') or 'open'}",
            "rfi": r,
        })
    return chunks


_CHUNKS = _load_chunks()


def _retrieve(query: str, k: int = 5):
    q = set(query.lower().split())
    scored = []
    for c in _CHUNKS:
        overlap = len(q & set(c["text"].lower().split()))
        if overlap:
            scored.append((overlap, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:k]]


def ask(query: str):
    ctx = _retrieve(query)
    context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in ctx)
    prompt = (
        f"Answer the project question using ONLY the context. Cite sources in "
        f"square brackets like [specs/UPS.md]. If a prior RFI is relevant, say so.\n\n"
        f"=== CONTEXT ===\n{context}\n\n=== QUESTION ===\n{query}"
    )
    answer = complete(prompt, system="You are a precise EPC project copilot. "
                                      "Cite every claim.", json_mode=False)
    prior_rfis = [c["rfi"] for c in ctx if "rfi" in c]
    return {"answer": answer,
            "sources": [c["source"] for c in ctx],
            "prior_rfis": prior_rfis}
