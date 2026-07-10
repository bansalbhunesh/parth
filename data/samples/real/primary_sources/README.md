# Primary Sources — Stored Verbatim, Not Team-Authored

Everything else under `data/samples/real/` is team-authored prose whose
*values* are cited from public sources but whose *text* was written by this
team (see `../PROVENANCE.md`). That is a legally safe way to reference
copyrighted manufacturer datasheets and paywalled standards (ASHRAE, NFPA,
Uptime Institute, IEC) without reproducing them — but it means, as an
external audit correctly pointed out, the benchmark stored zero original
primary-source files.

This directory is the answer to that gap, scoped to what's actually legal:
**U.S. federal regulatory text**, which is a government edict and not
subject to copyright (*Georgia v. Public.Resource.Org*, 139 S. Ct. 1743
(2020)). That is a narrow lane — it does not solve the vendor-datasheet or
paywalled-standard problem, and this README says so rather than implying
otherwise. Each file's own header states its specific license basis,
retrieval method (reproducible via the eCFR's public API), and retrieval
date.

| File | Backs | Note |
|---|---|---|
| `40_CFR_60_Subpart_IIII.md` | The "EPA Tier 4" generator-emissions requirement in `../design_basis_helios.md` (Pair 1) | Reveals the design-basis document's Tier 4 line is a stricter-than-federal-code project choice, not a claim about the regulatory floor — see the file's own header |
| `40_CFR_98_Table_A-1_GWP.md` | The R-134a / HFC-227ea (FM-200) GWP claims in `../PROVENANCE.md` (Pairs 4–5) | Values here differ from the AR4-vintage figures already cited elsewhere in this repo — disclosed as an open reconciliation item in the file's own header, not silently resolved |

Neither file is wired into the frozen `benchmarks/ps4_external_v1` scoring
corpus yet — they exist as evidence for reviewers to check the two claims
above against a primary source, and as a base for a future eval tier built
from documents that never informed the reconcile prompt's tuning, if that's
the direction taken next.
