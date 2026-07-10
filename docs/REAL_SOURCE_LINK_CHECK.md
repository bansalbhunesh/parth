# Real Source Link Check

Checked at: 2026-07-10T05:49:17Z

Scope: public links listed in `data/samples/real/PROVENANCE.md`.

This report verifies that the cited public provenance links are resolvable or explicitly need manual browser review. It does not store or redistribute third-party PDFs, does not validate licensed standards text, and does not convert team-authored fixtures into real customer/vendor submittals.

Summary: 13 ok, 6 manual browser checks, 0 unreachable.

| Source | Supports | Status | Detail |
|---|---|---|---|
| Vertiv Liebert GXT5 product family page | GXT5 online efficiency, runtime table, PF (Pair 1) | manual_check | HEAD HTTP 403: Forbidden |
| Cummins QSK60 generator page | QSK60 ratings, NFPA 110 material (Pair 1) | manual_check | HEAD HTTP 403: Forbidden |
| STULZ CyberAir CW & DX (STULZ USA) | EC-fan CRAC/CRAH family, DX/R410A (Pair 2) | ok | HEAD HTTP 200 |
| ABB MNS product page | MNS LV switchgear family (Pair 3) | manual_check | GET ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host |
| ABB MNS System Guide (1TGC902030B0204) | Icw up to 100 kA, Form up to 4, IEC 61439-1/-2, IEC 61641 variant (Pair 3) | ok | HEAD HTTP 200 |
| EPA GWP reference page | R-410A 2,088 · R-134a 1,430 · HFC-227ea/FM-200 3,220 (AR4 values; Pairs 2/4/5) | ok | HEAD HTTP 200 |
| eCFR 40 CFR 60 Subpart IIII | Stationary CI engine emission tiers (Pair 1) | ok | HEAD HTTP 200 |
| EUROBAT VRLA guide (2022, official PDF) | 3–5 yr "Standard Commercial" design-life class (Pair 6) | ok | HEAD HTTP 200 |
| Tate ConCore 1250 product page | 1,250 lbf concentrated-load class (Pair 9) | ok | HEAD HTTP 200 |
| Tate ConCore 1250 spec sheet (R07/15 mirror) | CISCA concentrated/ultimate load figures (Pair 9) | ok | HEAD HTTP 200 |
| Schneider Canalis KTA 800–5000 A catalogue (DEBU021EN) | KTA10 Icw 50 kA/1 s (Pair 10) | ok | HEAD HTTP 200 |
| LBL / ASHRAE thermal guidelines PDF | Class A1 recommended vs allowable envelopes (Pair 11) | ok | HEAD HTTP 200 |
| Raritan PX3 page | PX3-1000 inlet metering; outlet metering/switching are 5000-series (Pair 12) | ok | HEAD HTTP 200 |
| Xtralis VESDA VLC page | VLC 800 m² published coverage ceiling (Pair 13) | ok | HEAD HTTP 200 |
| Distech ECB-600 product page | ECB-600 series controller (Pair 14) | manual_check | HEAD HTTP 403: Forbidden |
| Distech ECB B-AAC PICS (official PDF) | BTL B-AAC profile on BACnet MS/TP (Pair 14) | manual_check | HEAD HTTP 405: Method Not Allowed |
| energy-storage.news: Samsung SDI first to pass UL 9540A | 128S/136S rack-level UL 9540A first (Pair 15) | manual_check | HEAD HTTP 403: Forbidden |
| cleanpower.org NFPA 855 safety summary (PDF) | NFPA 855 ESS limits context (Pair 15) | ok | HEAD HTTP 200 |
| Mayfield Renewables: NFPA 855 fire codes article | NFPA 855 spacing/limits context (Pair 15) | ok | HEAD HTTP 200 |

Policy:
- `ok` means the URL responded with a 2xx/3xx status during this run.
- `manual_check` means the host blocked automated verification or requires a browser/session; the citation must remain labeled as manual-checkable.
- `unreachable` means the citation should not be used for a new public claim until it is repaired or replaced.
- Source values still need human engineering review before they are treated as externally validated ground truth.
