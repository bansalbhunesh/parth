# Standards & Source Limitations

This document states exactly what the Pramaan documents and the ps4_external_v1
benchmark are — and are not — so no reader (or judge) over-reads the provenance.
For the consolidated provenance + claim-governance index (with per-manifest
stats), see [`SOURCE_PROVENANCE.md`](SOURCE_PROVENANCE.md).

## Key distinctions (read these first)

1. **An owner design basis is NOT a public standard.** The `owner_requirement.md`
   files are *team-authored design-basis fixtures* expressing an owner's design
   intent. They are not reproductions of any published standard, and their
   values are not "the standard's requirement."

2. **A team-authored fixture is NOT a vendor datasheet.** The
   `vendor_submittal.md` files (and the rendered `vendor_submittal.png` image
   pairs) are *synthetic fixtures* modeled to exercise deviation types. They are
   **not** real vendor datasheets, real submittals, or real unseen documents.

3. **"Primary-source-derived" is NOT "stored primary-source file."** Ten
   benchmark documents are *derived from* public primary-source values (e.g. a
   published GWP figure or an emissions-standard threshold); five manifest rows
   cite a verified public URL. Deriving a value from a public source is **not**
   the same as storing that source's PDF. **No primary-source PDFs are stored or
   redistributed in this repository unless the license/usage basis permits it.**

4. **Proprietary standards are citation-only / paraphrase-only.** Where a
   proprietary standard is relevant (e.g. Uptime Institute Tier classifications,
   TIA-942, BICSI-002, NFPA 75/76, IEC series, ASHRAE TC9.9, IS 1893), it is
   referenced **by name and clause only**, or paraphrased. **No proprietary
   standard text is copied or redistributed** anywhere in this repository.

5. **Public URLs are used for provenance where available.** Government/public
   sources (e.g. EPA eCFR 40 CFR 60 Subpart IIII, EPA GWP guidance, the
   LBNL/ASHRAE thermal-guidelines PDF) are cited with a retrieved public URL in
   the benchmark manifest, so a reviewer can check the derivation. The broader
   real-sample source list is re-checkable with
   `python scripts/check_real_source_links.py`; pages that block automated
   fetching must remain labeled as manual browser checks.

6. **Trademarks belong to their owners.** All product, vendor, and standards-body
   names are trademarks of their respective owners, used here nominatively for
   identification only.

7. **No endorsement is implied.** Nothing here implies that any vendor,
   standards body, or organization endorses, sponsors, or has reviewed Pramaan.

## What this means for claims

- The benchmark is an **independent, provenance-tracked, team-authored**
  evaluation set — not a corpus of real datasheets.
- Benchmark numbers are **benchmark results**, not real-world or field-validated
  accuracy. See [`docs/CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md) for the exact
  allowed/banned wording.
- Provenance and review status are tracked in
  `benchmarks/ps4_external_v1/labels/REVIEW_STATUS.md` and the manifest.
- Public-link availability is tracked in `docs/REAL_SOURCE_LINK_CHECK.md`.
  Link availability is evidence for traceability, not a substitute for
  independent engineering review.
