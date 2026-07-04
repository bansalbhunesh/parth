# Third-Party Notices

Pramaan uses third-party software, references published standards, and derives
some benchmark values from public sources. This file acknowledges them. See
[`docs/STANDARDS_AND_SOURCE_LIMITATIONS.md`](docs/STANDARDS_AND_SOURCE_LIMITATIONS.md)
for what the benchmark provenance does and does not mean, and
[`docs/SOURCE_PROVENANCE.md`](docs/SOURCE_PROVENANCE.md) for the consolidated
provenance-and-claim-governance index.

## Software dependencies

Each dependency is distributed under its own license, held by its respective
authors. Consult each project for exact terms; this list is informational.

| package | typical license |
|---|---|
| fastapi, starlette | MIT |
| uvicorn | BSD-3-Clause |
| pydantic | MIT |
| google-genai | Apache-2.0 |
| anthropic | MIT |
| langgraph | MIT |
| numpy | BSD-3-Clause |
| networkx | BSD-3-Clause |
| **pymupdf (PyMuPDF / MuPDF)** | **AGPL-3.0 (or commercial)** — see note |
| pdfplumber | MIT |
| pytesseract (wrapper for Tesseract OCR) | Apache-2.0 / MIT |
| Pillow | MIT-CMU (HPND) |
| python-multipart | Apache-2.0 |
| httpx | BSD-3-Clause |
| openai | Apache-2.0 / MIT |

**Note on PyMuPDF:** PyMuPDF/MuPDF is AGPL-3.0-licensed (a commercial license is
available from Artifex). Any redistribution or hosted-service use should confirm
AGPL compliance or obtain a commercial license. Flagged here for IP hygiene.

## Standards referenced (citation-only / paraphrase-only)

The following standards are referenced **by name and clause only**, or
paraphrased for interpretation. **No standard text is copied or redistributed.**
Each is the property of its publishing body, and its name is a trademark of that
body:

- Uptime Institute — Tier Classification (Tier III / IV)
- TIA-942 (Telecommunications Infrastructure Standard for Data Centers)
- BICSI-002
- NFPA 75 / NFPA 76
- IEC (relevant series, e.g. switchgear/UPS)
- ASHRAE TC9.9 (Thermal Guidelines for Data Processing Environments)
- IS 1893 (seismic)

No endorsement, sponsorship, or review by any of these bodies is implied.

## Public data sources (used for benchmark provenance)

Where a benchmark value is derived from a public primary source, the manifest
records a retrieved public URL. Public sources referenced include:

- U.S. EPA — eCFR, 40 CFR 60 Subpart IIII (emissions) — ecfr.gov
- U.S. EPA — Understanding Global Warming Potentials — epa.gov
- LBNL / ASHRAE TC9.9 Thermal Guidelines (public PDF) — datacenters.lbl.gov

These are cited for provenance only; **no primary-source PDF is stored or
redistributed** in this repository (see the source-limitations doc).

## Trademarks

All product, vendor, service, and standards-body names are trademarks or
registered trademarks of their respective owners, used nominatively for
identification only. Their use does not imply any affiliation with or endorsement
by those owners.
