# Competitive repository scan — 2026-07-15

This is a dated, reproducible public-repository snapshot, not a judge ranking or
product-accuracy comparison. Private submissions, unindexed repositories,
deployed products behind a login, and work pushed after the snapshot are outside
its visibility. A missing public test, evaluation, or workflow means only that
the scanner did not find one in the visible repository.

## Reproduce the census

The scan was generated from GitHub's public repository and tree APIs with the
tracked [`scripts/audit_et_hackathon_field.py`](../scripts/audit_et_hackathon_field.py)
scanner:

```powershell
$env:GITHUB_TOKEN = gh auth token
python scripts/audit_et_hackathon_field.py `
  --markdown "$env:TEMP\parth_competitive_census_2026-07-15.md" `
  --json "$env:TEMP\parth_competitive_census_2026-07-15.json" `
  --workers 12
```

Snapshot result: **357 unique public candidates** — 119 found by exact event-name
queries and 238 additions found by problem-title queries. The confidence split
was 149 high, 167 medium, and 41 low; 14 repositories were classified as PS4.
The full generated files are intentionally output artifacts rather than source
files. This concise record stores the conclusions that affect product decisions;
the command above regenerates the underlying rows.

The scanner's `evidence_index` rewards visible code, tests, evaluation artifacts,
architecture, deployment/run instructions, and repository hygiene. It does
**not** measure usefulness, model accuracy, design quality, live reliability, or
judge preference. File counts are API-tree heuristics, not passing-test counts.

## Census result

| Public evidence-index rank | Repository | Index | Visible evidence at snapshot |
|---:|---|---:|---|
| 1 | [`bansalbhunesh/parth`](https://github.com/bansalbhunesh/parth) | 97 | PS4; code, tests, frozen evaluation data, architecture, impact and run artifacts |
| 2 | [`DKDVE/et-hackathon`](https://github.com/DKDVE/et-hackathon) | 82 | Broad operational-context platform; substantial code and test surface; three workflow files |
| 3 | [`roybishal362/VayuNetra-Urban-Air-Quality-Intelligence`](https://github.com/roybishal362/VayuNetra-Urban-Air-Quality-Intelligence) | 79 | PS5; code, tests, workflow and architecture evidence |
| 4 | [`9SERG4NT/vayunetra`](https://github.com/9SERG4NT/vayunetra) | 78 | PS5; code and test evidence |
| 5 | [`Mukilan-s18/Industrial-Operations-Brain`](https://github.com/Mukilan-s18/Industrial-Operations-Brain) | 77 | PS1/PS8; broad code and test surface |

Pramaan ranked first in this repository-evidence index. That supports a claim
about the completeness of its visible proof package only; it is not evidence of
first place in the hackathon.

## Direct PS4 field

| PS4 repository | Evidence index | Scanner-visible tests / CI | Current interpretation |
|---|---:|---:|---|
| `bansalbhunesh/parth` | 97 | 46 / 1 | Deepest public reproducibility and benchmark package in this snapshot |
| `suryanshvermaa/DCBrain` | 67 | 23 / 0 | Closest direct feature-surface rival: compliance, schedule, procurement, RFI and dashboard breadth |
| `09singh/AI-Data-Centre-EPC` | 52 | 10 / 0 | Meaningful implementation and tests; narrower visible evidence package |
| `Sanket-2736/AI-Intelligence-Platform-for-Data-Centre-EPC-Project-Delivery` | 48 | 0 / 0 | Product implementation without a visible automated proof layer |
| Remaining 10 classified PS4 repositories | 0–37 | 0 / 0 | Smaller, documentation-led, or empty public surfaces at snapshot time |

## Exact-head verification of the closest and most instructive repositories

The census is broad and heuristic. The following repositories were also checked
out at the listed commits and exercised with their own available commands. A
timeout is recorded as a timeout, not converted into a failure or a pass.

| Repository (commit) | What passed | What did not pass or was absent | Pattern worth adopting |
|---|---|---|---|
| `DKDVE/et-hackathon` (`0fb48d708c30`) | Frontend typecheck; 18 of 20 frontend tests | Two tests failed because `sessionStorage` was unavailable; lint emitted five warnings; the inspected GitHub CI run was red; no automated accessibility suite was found | Treat operational context as a first-class object and keep strong workflow-level test organization |
| `suryanshvermaa/DCBrain` (`f1caf1925280`) | Broad 16-page product surface | Workflows were under `workflows-disabled`; frontend typecheck, the only frontend test, and production build failed; clean installs reported critical/high advisories; backend build/test did not finish within four minutes | Keep its useful schedule/procurement/RFI information architecture, but require a smaller passing surface and evidence gates |
| `sanskar9999/prahari` (`19df80cc2189`) | Clean production build and a successful Pages deployment workflow | No tracked tests or automated accessibility suite; install audit reported one high and three moderate advisories | Preserve its short guided demo and immediate problem framing |
| `Agent-A345/PlantIQ` (`f5c23a445f2c`) | Python compilation | No tracked tests or active CI; the principal HTML and graph modules were very large | Preserve its explicit separation of real regulatory sources from simulated telemetry |
| `Exyons/ET-GenAI-Hackathon` (`b44856e57125`) | Production build | Lint reported 18 errors and four warnings; install audit reported one high and one moderate advisory; no tracked tests | Use channel breadth only when it directly matches user constraints |
| `FinTwin` (`0e1a97edc721`) | Production build, with warnings | Strict typecheck failed with three errors; audit reported five high, five moderate and two low advisories; no tracked tests | Its financial consequence framing is useful, but evidence must remain adjacent to the number |
| `Janicebenita/AI-powered-Industrial-Knowledge-Intelligence` (`46d74cc1fcb0`) | Nine tracked test files were visible | No active CI or automated accessibility suite was found | Maintain a domain-object taxonomy without multiplying unverified agents |
| `Alekhya-S-hub/psc-submittals-git` (`784c085985de`) | MIT-licensed deterministic CSI hierarchy extraction is inspectable | Its reported 94.3 F1 on 20 real specs was not accompanied by a shipped test/evaluation corpus | Adopt the bounded deterministic-enumeration pattern, not the unverified score |

Dependency-audit results are time-dependent and ecosystem advisories change. They
describe the clean install at this snapshot, not a permanent property of another
team's repository.

## Decisions for this branch

1. **Adopted — prompt-path isolation.** The omission-recall coverage matrix is an
   explicit candidate prompt version. Live analysis and the public benchmark now
   share one prompt builder, while baseline mode remains byte-identical and clears
   the candidate flag. Candidate output cannot overwrite a baseline run directory.
2. **Adopted — evidence-scoped positioning.** DKDVE and DCBrain are named threats;
   repository-index leadership is kept separate from product and judge claims.
3. **Adopted — guided proof.** Pramaan keeps the short evidence → consequence →
   owner → RFI → closure journey seen in the clearest competitor demos.
4. **Rejected — feature-count competition.** DCBrain and PlantIQ demonstrate how
   breadth can outrun passing verification. New surfaces require route, type,
   accessibility, and browser evidence before they count as product strength.
5. **Rejected — benchmark promotion.** A same-day frozen LLM comparison found
   v1.7 recovered 8/8 omissions versus 7/8 for the contemporaneous baseline, but
   doubled clean-negative FAR from 0.0156 to 0.0312 without improving overall
   recall. It remains off by default; the full evidence is in
   `benchmarks/ps4_external_v1/reports/coverage_matrix_experiment_2026-07-15.md`.
6. **Deferred — field claims.** Practitioner review, pilots, independent WCAG
   review, penetration testing, and production load/restore evidence remain open
   external gates; repository depth cannot substitute for them.

## Bottom line

At this snapshot, the branch has the strongest public **reproducibility package**
found in PS4 and the highest all-track repository-evidence index. DKDVE is the
closest repository-engineering rival and DCBrain is the closest direct PS4
feature rival. Neither fact proves that Pramaan is the best product or will win;
the remaining route to a defensible 10/10 is measured candidate-benchmark gain
plus independent accessibility, security, reliability, restore and field proof.
