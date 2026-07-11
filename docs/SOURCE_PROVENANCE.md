# Source Provenance & Governance

The single index for **where every value in Pramaan's evaluation set comes
from**, and the governance rules for how it may be described. Written so a judge
can cross-examine provenance and get consistent, honest answers.

**Authoritative records** (this doc summarizes; these are the source of truth):
- Machine-readable manifest: [`benchmarks/ps4_external_v1/manifest.csv`](../benchmarks/ps4_external_v1/manifest.csv)
  (per-file `source_origin`, `source_url`, `source_owner`, `retrieval_date`,
  `sha256`, `license_or_usage_basis`, `primary_or_secondary`).
- Real-pair provenance narrative: [`data/samples/real/PROVENANCE.md`](../data/samples/real/PROVENANCE.md).
- Public-link verification report: [`REAL_SOURCE_LINK_CHECK.md`](REAL_SOURCE_LINK_CHECK.md),
  generated from the real-pair provenance links by
  `python scripts/check_real_source_links.py`.
- Review status: [`benchmarks/ps4_external_v1/labels/REVIEW_STATUS.md`](../benchmarks/ps4_external_v1/labels/REVIEW_STATUS.md).
- Standards/IP: [`../THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md),
  [`STANDARDS_AND_SOURCE_LIMITATIONS.md`](STANDARDS_AND_SOURCE_LIMITATIONS.md).
- Claim wording: [`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md) (the governing
  allowed/banned table).

---

## 1. The seven distinctions (say these exactly)

1. **Owner design basis ≠ public standard.** `owner_requirement` / design-basis
   files express a team-authored owner *design intent*; their values are not
   "the standard's requirement."
2. **Team-authored fixture ≠ vendor datasheet.** The submittal files/images are
   *synthetic engineering documents* modeled to exercise deviation types — not
   real vendor datasheets, submittals, or unseen documents.
3. **Primary-source-derived ≠ stored primary-source file — true of the frozen
   benchmark manifest specifically.** Within the 106-row manifest, values are
   *derived from* public figures, marked `primary_derived` / `secondary`; **no
   primary-source PDF is stored or redistributed as part of the frozen
   benchmark.** Separately, and outside the manifest entirely, two U.S. federal
   regulatory documents ARE now stored **verbatim** under
   [`data/samples/real/primary_sources/`](../data/samples/real/primary_sources/) —
   legal only because federal regulatory text is a government edict, not
   copyrightable (*Georgia v. Public.Resource.Org*, 139 S. Ct. 1743 (2020));
   this does not extend to vendor datasheets or paywalled standards, which
   remain citation-only for the reason in point 4 below. See that directory's
   own `README.md` for the exact scope.
4. **Proprietary standards = citation-only / paraphrase-only.** Standards are
   referenced by name/clause or paraphrased for interpretation. **No proprietary
   standard text is copied or redistributed** (every manifest row's
   `license_or_usage_basis` states "no proprietary standard text copied").
5. **Public URLs are used for provenance where available.** Government/public
   sources carry a retrieved `source_url` in the manifest so a reviewer can check
   the derivation. The real-sample narrative also has an automated link-check
   report; browser-blocked vendor pages stay labeled as manual-checkable rather
   than silently treated as verified downloads.
6. **Trademarks belong to their owners.** All product/vendor/standards-body names
   are used nominatively for identification only; **no endorsement is implied**.
7. **Benchmark limitations stay visible.** These are team-authored fixtures;
   numbers are benchmark results, not real-world/field-validated accuracy;
   reviewer-2 human adjudication is pending.

---

## 2. Provenance status (from the manifest, 106 rows)

| Property | Status |
|---|---|
| `source_origin` | all **team-authored** (`owner_design_basis_team_authored`, `team_authored_from_public_values`, `adversarial_team_authored`, `synthetic_negative`) |
| `primary_or_secondary` | `primary_derived` or `secondary` — **none of these 106 rows are stored primary files** (two *are* stored, verbatim, outside the manifest — see point 3 above) |
| Verified public `source_url` | **5** manifest rows carry a checkable public URL; the broader real-sample narrative has a separate public-link check report |
| Proprietary standard text | **none copied/redistributed** (per every row's `license_or_usage_basis`) |
| `sha256` per file | present (integrity; verified by `scripts/benchmark_hash_sources.py`) |
| Human review | single-author frozen; **reviewer-2 adjudication pending** |

Public sources cited for derivation within the 106-row manifest (provenance
only, no file stored there): U.S. EPA eCFR 40 CFR 60 Subpart IIII; EPA GWP
guidance; LBNL/ASHRAE TC9.9 thermal guidelines. Two of these — 40 CFR 60
Subpart IIII and the 40 CFR 98 Table A-1 GWP table — are additionally stored
verbatim outside the manifest, under `data/samples/real/primary_sources/`
(see point 3 above); the manifest-row citations above are unchanged by that
addition. Vendor product *values* are cited from public manufacturer
literature (Vertiv, Cummins, STULZ, ABB, Raritan, Xtralis, Distech, Samsung SDI,
Tate, Schneider) — see `data/samples/real/PROVENANCE.md` for the per-value
citation. Standards named (paraphrased only): Uptime Tier IV, TIA-942, BICSI-002,
NFPA 75/76/110/2001/855, IEC 61439/61641/60076, IEEE 519/1188, ASHRAE 90.1/TC9.9,
IS 1893, EU F-Gas, US AIM Act.

Automated provenance re-check: run
`python scripts/check_real_source_links.py` to refresh
`docs/REAL_SOURCE_LINK_CHECK.md`. This check proves URL availability only. It
does not redistribute third-party source files, validate licensed standards
text, or replace human engineering review.

---

## 3. Claim governance (allowed / banned / evidence / nearby limitation)

`CLAIMS_REGISTER.md` is the governing table; the provenance-specific rows:

| Topic | Allowed wording | Banned wording | Evidence | Limitation that MUST appear nearby |
|---|---|---|---|---|
| Fixtures | "team-authored fixtures modeled on public reference values" | "real vendor datasheets", "real unseen submittals" | manifest `source_origin` | this *is* the limitation — fixtures, not real files |
| Primary-source derivation | "derived from public primary sources; 5 cite a verified public URL" | "10 stored primary-source PDFs", "real datasheets" | manifest `source_url` (5), `primary_or_secondary` | derived ≠ stored |
| Design basis | "team-authored owner design-basis fixture" | "the standard requires X" (when it's the owner basis) | design-basis files | owner intent ≠ published standard |
| Standards | "references Uptime/TIA-942/NFPA/… by name and clause; paraphrased" | quoting/reproducing standard text | `license_or_usage_basis` | no proprietary text redistributed |
| Trademarks | "used nominatively for identification only" | anything implying endorsement/affiliation | THIRD_PARTY_NOTICES | no endorsement implied |
| Benchmark result | "benchmark result on ps4_external_v1" | "real-world accuracy", "field-validated" | benchmark_card.json | team-authored; reviewer-2 pending |

Enforcement: banned phrases are grep-listed in `CLAIMS_REGISTER.md`; benchmark
integrity is checked by `scripts/benchmark_manifest_check.py` +
`benchmark_hash_sources.py`.

---

## 4. What is NOT claimed
- No proprietary standard text is redistributed anywhere in the repo.
- No stored primary-source vendor PDFs — only derived, cited values. (Two
  federal *regulatory* documents ARE stored verbatim, outside the manifest —
  government edicts are not copyrightable, unlike vendor literature; see
  point 3 in section 1.)
- No vendor/standards-body endorses, sponsors, or has reviewed Pramaan.
- No real-world or field-validation claim is made from the benchmark numbers.
