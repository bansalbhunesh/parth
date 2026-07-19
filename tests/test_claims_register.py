"""Claims-register enforcement gate — makes "grep-enforced" actually true.

docs/CLAIMS_REGISTER.md defines wording that must never appear affirmatively on
any public-facing surface (README, pitch, deck source, docs, frontend text,
benchmark reports). Until this test existed the register *said* the list was
grep-enforced but nothing enforced it — which is exactly how an affirmative
"every edge is standards-cited" slipped into docs/PS4_ALIGNMENT.md.

Contract:
- A banned phrase on a scanned line FAILS unless a negation / governance
  marker ("not", "never", "banned", "❌", "pending", …) precedes it in the
  SAME sentence (or a governance marker follows right after) — i.e.
  disclaimers like "this is NOT a field-validated claim" stay legal,
  affirmative use does not. An unrelated negation in an earlier sentence on
  the same line does not launder the phrase (the exact failure mode of the
  PS4_ALIGNMENT.md slip: "…not a point forecast. Every edge is
  standards-cited…").
- Governance/historical files that must quote the banned list verbatim
  (CLAIMS_REGISTER itself, SOURCE_PROVENANCE's allowed/banned table, the
  retired-claims audit record) are exempt by name, with the reason stated.
- The scan is line-based and best-effort: a phrase split across a line break
  is not caught. Keep banned-list quotations on a single line with their
  negation marker (see docs/SECURITY_DEMO_RUNBOOK.md's "never say" list).
"""

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Public-facing surfaces under the claims register. Globs are resolved
# relative to the repo root; missing files are skipped silently.
SCANNED_GLOBS = [
    "README.md",
    "PITCH.md",
    "COMPETITIVE.md",
    "presentation.html",
    "docs/*.md",
    "docs/*.html",
    "frontend/app/**/*.tsx",
    "frontend/components/*.tsx",
    "frontend/lib/*.ts",
    "benchmarks/ps4_external_v1/**/*.md",
    "data/samples/**/*.md",
    "eval/*.md",
]

# Files allowed to quote banned wording without a per-line negation marker.
EXEMPT = {
    # The register itself — it defines the banned list.
    "docs/CLAIMS_REGISTER.md",
    # Allowed-vs-banned wording table (claims governance index).
    "docs/SOURCE_PROVENANCE.md",
}
# Untracked local notes may sit under docs/_local_* (gitignored); exempt by
# prefix so a local run matches CI.
EXEMPT_PREFIXES = ("docs/_local_",)

# Negation / governance markers that make a banned phrase a legal disclaimer.
# PRE markers must precede the phrase in the same sentence; POST markers
# (labels like "banned") may follow it immediately.
NEGATION_RX = re.compile(
    r"\bnot\b|\bnever\b|\bno\b|n[’']t\b|\bbanned\b|\bavoid\b|❌|\bpending\b"
    r"|\bwithout\b|\brather than\b|\binstead of\b|\bretired\b|\bdo[\s-]not\b"
    r"|\bnor\b|\bnon-claim|\bcannot\b|\bmust never\b",
    re.IGNORECASE,
)
POST_MARKER_RX = re.compile(r"\bbanned\b|❌|\bavoid\b|\bnever\b|\bretired?\b",
                            re.IGNORECASE)
# A whole line that is explicitly a governance list ("Banned wording — …",
# "❌ …", "never say …") may quote phrases anywhere on the line.
GOVERNANCE_LINE_RX = re.compile(
    r"\bbanned\b|❌|\bnever say\b|\bdo (?:not|n[’']t) say\b|\bwhat not to claim\b",
    re.IGNORECASE,
)
# "…independently reviewed?" — Not yet."  A question answered immediately in
# the negative on the same line is a disclaimer, not a claim.
QNA_NEGATIVE_RX = re.compile(
    r"^[^.!?]{0,60}\?(\s*</?\w[^>]*>)*[\s\"'”’)\]—–-]{0,10}(no|not)\b",
    re.IGNORECASE,
)
SENTENCE_BOUNDARY_RX = re.compile(r"[.!?](\s|$)")
_PRE_WINDOW = 80   # chars before the phrase a negation may sit in
_POST_WINDOW = 40  # chars after the phrase a governance label may sit in


def _is_governed(squashed: str, start: int, end: int) -> bool:
    """True if the banned-phrase match at [start:end) is negated/governed:
    a negation marker before it in the same sentence; a governance label
    ("banned", ❌, "retired", …) right after it in the same sentence; a
    governance-list line; or a question answered immediately in the negative."""
    if GOVERNANCE_LINE_RX.search(squashed):
        return True
    pre = squashed[max(0, start - _PRE_WINDOW):start]
    for m in NEGATION_RX.finditer(pre):
        between = pre[m.end():]
        if not SENTENCE_BOUNDARY_RX.search(between):
            return True
    post = squashed[end:end + _POST_WINDOW]
    m = POST_MARKER_RX.search(post)
    if m and not SENTENCE_BOUNDARY_RX.search(post[:m.start()]):
        return True
    if QNA_NEGATIVE_RX.match(squashed[end:]):
        return True
    return False

# Banned wording, as regexes over a whitespace-normalized, lowercased line.
# Sources: docs/CLAIMS_REGISTER.md "Do NOT say" + architecture claims table
# + near-miss phrasing the 2026-07-06 audit found in the wild.
BANNED = [
    (r"real[\s-]world[\s-]accuracy", "claims #6/16: no real-world-accuracy claim"),
    (r"real\s+unseen\s+datasheets?", "claims #18: fixtures are team-authored"),
    (r"unseen[\s-](datasheets?|documents?|submittals?)", "near-miss of #18: nothing is 'unseen'"),
    (r"held[\s-]out", "labels are frozen, not held-out (same team authored engine + labels)"),
    (r"field[\s-]validat", "claims #16: no field validation exists"),
    (r"production[\s-](grade|ready)", "claims #17: prototype only"),
    (r"100%\s*recall", "claims #6"),
    (r"zero\s+false\s+positives\s+overall", "claims #9: FAR is clean-negative-only"),
    (r"customer\s+roi", "claims #19"),
    (r"fully\s+independent\s+benchmark", "claims register: benchmark is team-authored"),
    (r"(two[\s-](reviewer|person))[\s-]adjudicated", "claims #14: reviewer-2 pending"),
    (r"independent(ly)?\s+(reviewed|validated|adjudicated|human[\s-]adjudicated)",
     "claims #14: no independent review has happened"),
    (r"stored\s+primary[\s-]source\s+benchmark", "claims #15: stored PDFs pending"),
    (r"ocr\s+works\s+everywhere", "claims #20"),
    (r"reads?\s+any\s+scanned\s+pdf", "claims #20"),
    (r"(pixel[\s-]perfect|lossless)\s+ocr", "claims #20"),
    (r"100%\s*ocr\s*accuracy", "claims #20"),
    (r"(failover\s+improves|more\s+accurate\s+with\s+failover)", "claims #22: availability only"),
    (r"never\s+goes\s+down", "claims #22"),
    (r"100%\s*uptime", "claims #22"),
    (r"secure\s+by\s+default", "claims #23"),
    (r"penetration[\s-]tested", "claims #23"),
    (r"zero\s+vulnerabilities", "claims #23"),
    (r"ddos\s+protection", "claims #23: rate limiting is not DDoS protection"),
    (r"hardened\s+against\s+all\s+attacks", "claims #23"),
    (r"(five|5)\s+(ai\s+)?(autonomous\s+)?agents", "claims A1: one reasoning graph, not five agents"),
    (r"multi[\s-]agent\s+ai\s+system", "claims A1"),
    (r"fully\s+autonomous", "claims A1"),
    (r"(every|all)\s+(graph\s+)?edges?\s+(is\s+|are\s+)?standards[\s-]cited",
     "claims A5: structural edges carry no basis"),
    (r"battle[\s-]tested", "claims #5 banned wording"),
    (r"extensively\s+benchmarked", "claims #5 banned wording"),
]
BANNED_RX = [(re.compile(rx, re.IGNORECASE), why) for rx, why in BANNED]


def _scanned_files() -> list[pathlib.Path]:
    seen: set[pathlib.Path] = set()
    for pattern in SCANNED_GLOBS:
        for p in sorted(ROOT.glob(pattern)):
            rel = p.relative_to(ROOT).as_posix()
            if rel in EXEMPT or rel.startswith(EXEMPT_PREFIXES):
                continue
            if p.is_file():
                seen.add(p)
    return sorted(seen)


def _violations() -> list[str]:
    out = []
    for path in _scanned_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            # Normalize markdown emphasis + smart quotes so "**not**" and
            # curly apostrophes don't defeat either the ban or the negation.
            norm = re.sub(r"[*_`]", "", line).replace("’", "'")
            squashed = re.sub(r"\s+", " ", norm)
            for rx, why in BANNED_RX:
                m = rx.search(squashed)
                if m and not _is_governed(squashed, m.start(), m.end()):
                    out.append(f"{rel}:{lineno}: banned wording {rx.pattern!r} ({why})\n"
                               f"    {line.strip()[:160]}")
    return out


def test_scan_covers_the_core_surfaces():
    """The gate must actually be looking at the headline surfaces."""
    rels = {p.relative_to(ROOT).as_posix() for p in _scanned_files()}
    for must in ("README.md", "PITCH.md", "presentation.html",
                 "docs/PS4_ALIGNMENT.md", "frontend/app/judge/page.tsx",
                 "frontend/app/evidence/page.tsx"):
        assert must in rels, f"claims gate no longer scans {must}"

    competitive = (ROOT / "COMPETITIVE.md").read_text(encoding="utf-8")
    for retired_overclaim in (
        "We are the only one you can actually check",
        "Pramaan is the only entrant",
    ):
        assert retired_overclaim not in competitive


# Public surfaces describe the product and the commercial market — never
# internal research into other hackathon entries. These patterns lock that
# boundary: if any of them reappears on a scanned surface, the build fails.
FIELD_RESEARCH_RX = [
    re.compile(rx, re.IGNORECASE)
    for rx in (
        r"repo(?:sitory)?\s+census",
        r"hackathon[\s-]field",
        r"ranked\s+first",
        r"evidence\s+index",
        r"competitor[\s-]inspired",
        r"field\s+survey",
        r"rival\s+repo",
        r"scores?\s+rival",
        r"win[\s-]probability",
        r"scanned\s+repositor",
    )
] + [re.compile(r"Competitor [A-E]\b")]


def test_no_field_research_wording_on_public_surfaces():
    """No public surface may describe internal research into other entries."""
    offenders: list[str] = []
    for path in _scanned_files():
        rel = path.relative_to(ROOT).as_posix()
        for n, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            for rx in FIELD_RESEARCH_RX:
                if rx.search(line):
                    offenders.append(f"{rel}:{n}: {line.strip()[:100]}")
    assert not offenders, "field-research wording on public surfaces:\n" + "\n".join(
        offenders
    )


def _line_violates(line: str) -> bool:
    squashed = re.sub(r"\s+", " ", re.sub(r"[*_`]", "", line))
    for rx, _ in BANNED_RX:
        m = rx.search(squashed)
        if m and not _is_governed(squashed, m.start(), m.end()):
            return True
    return False


def test_gate_catches_an_affirmative_banned_phrase():
    """Self-test: an affirmative slip is caught; a genuine same-sentence
    disclaimer is allowed; an unrelated negation in a PREVIOUS sentence on
    the same line does not launder the phrase."""
    assert _line_violates(
        "Pramaan offers production-grade accuracy on real unseen datasheets.")
    assert not _line_violates(
        "This is NOT a production-grade product, and no datasheet is unseen.")
    # The exact PS4_ALIGNMENT.md failure mode: negation belongs to the prior
    # sentence, the banned claim is affirmative.
    assert _line_violates(
        "an upper bound, not a point forecast. Every edge is standards-cited")
    # Governance label after the phrase (a "banned wording" list) is allowed.
    assert not _line_violates('"production-grade" is banned wording here.')


def test_no_banned_claims_on_public_surfaces():
    """No affirmative banned wording anywhere a judge can read."""
    v = _violations()
    assert not v, ("Banned/overclaiming wording found (fix the wording or, for a "
                   "genuine disclaimer, keep its negation on the same line):\n"
                   + "\n".join(v))


@pytest.mark.parametrize("phrase", [
    # The wording slips the 2026-07-06 audit found in the wild, verbatim:
    "is an upper bound on schedule exposure, not a point forecast. "
    "Every edge is standards-cited",                       # PS4_ALIGNMENT.md
    "on held-out frozen labels.",                          # PITCH.md
    "the real proof is the unseen-document panel above.",  # judge page
    "FAR 0.000 on held-out labels",                        # COMPETITIVE.md
])
def test_gate_would_catch_the_2026_07_06_slips(phrase):
    """Regression: the wording slips the 2026-07-06 audit found must trip
    the gate if they ever come back."""
    assert _line_violates(phrase), phrase
