# Practitioner Validation — Outreach Kit

**Goal:** one quotable line from a named data-centre / MEP / commissioning
professional confirming the problem is real and Pramaan addresses it. This is the
single highest-leverage thing left — it moves the submission from "great build" to
"validated by the people who live this problem."

**Targeting (send 5–8 to land 1–2):** commissioning authorities (CxA), owner's
engineers, MEP design leads, data-centre project/construction managers, EPC QA/QC
leads. LinkedIn search: *"commissioning manager data center"*, *"MEP commissioning
authority"*, *"owner's engineer data centre India"*.

**Rules that get replies:** make the ask tiny (one line, not a meeting), do the
writing for them (offer a pre-drafted quote to approve/edit), be specific about
the problem, and give an easy out.

---

## Where to find them — named sources (fastest first)

**0. Your warm network (do this first).** You do NOT need a stranger. Anyone who
has done MEP / electrical / HVAC design or construction QA on *any* large facility
(not just data centres) is credible. Ask ex-colleagues, classmates now in
EPC/MEP, professors who consult for industry. A warm intro converts ~10× better
than a cold DM and is the only realistic path on a hackathon clock.

**1. Communities you can join today (highest reply rate):**
- **Infrastructure Masons (iMasons)** — global DC infra community, active Slack +
  India members; post the tiny ask in a relevant channel.
- **BICSI / BICSI India**, **7x24 Exchange**, **Uptime Institute** member network,
  **ASHRAE India** chapters — all full of CxAs and MEP leads.

**2. India DC operators (find their facilities / MEP / commissioning staff on LinkedIn):**
STT GDC India · CtrlS · Nxtra by Airtel · Yotta · NTT Global Data Centers India ·
Sify · Web Werks (Iron Mountain) · Pi Datacenters · AdaniConneX · Reliance Jio.

**3. EPC / MEP design-build & commissioning firms (India DC work):**
L&T Construction · Sterling & Wilson · Voltas · Blue Star · and the DC/MEP
practices at Jacobs, AECOM, WSP, Arup, Cundall, Mott MacDonald · plus the field-
services arms of **Vertiv / Schneider / ABB** (they commission this gear daily).

**4. Independent third-party commissioning (CxA) firms** — search LinkedIn for
*"commissioning authority data center"*, *"CxA data centre"*, *"owner's engineer
data center India"*, *"MEP commissioning manager"*.

**Who, exactly (titles to target):** Commissioning Authority / CxA · Owner's
Engineer · MEP Design Lead · Data-Centre Project/Construction Manager · EPC QA/QC
Lead · Critical-Facilities / Mission-Critical Engineer.

**The hook is now stronger** — point them at a concrete real pair: *"a Tate
ConCore 1250 panel (1250 lbf) proposed against a 1500 lbf high-density floor
spec, or a Canalis KTA10 at 50 kA against a 65 kA fault duty — does catching that
on submittal day match a review you've actually done?"* Specific beats abstract.

**Minimum bar for the submission:** ONE practitioner, even anonymised
("a CxA at a top-5 India colo"), even informal. That single line moves the
customer-validation score more than any further code.

---

## A. LinkedIn connection note (≤300 chars)

> Hi [Name] — I built a tool that reads vendor submittals against the design
> basis and flags deviations the day the document lands (e.g. a UPS rated 7-min
> battery vs a 10-min spec) before they surface in commissioning. You've lived
> this problem — could I get your 60-second reaction? No pitch.

## B. LinkedIn DM / short email (after they connect)

> Hi [Name],
>
> Quick one — I'd value your view as someone who actually runs [commissioning /
> MEP review / owner's engineering] on data-centre builds.
>
> I built **Pramaan**: it reads a vendor submittal against the design basis and
> the governing standards (Uptime, NFPA, ASHRAE, IEC…) and flags every deviation
> **the day the submittal arrives** — then tells you which commissioning test it
> would fail and how many weeks early you caught it. On a Vertiv-UPS + Cummins-genset
> pair (values cited from published datasheets) it flagged a 7-min battery vs a 10-min Tier-IV spec, a 95.9% vs 96%
> efficiency miss, a missing THD value, and EPA Tier 2 vs Tier 4 — and it can also
> read **scanned, image-only** submittals via OCR where Tesseract is installed.
>
> I'm not selling anything. I'd just like 60 seconds of honest reaction:
> **does this match a real pain you've seen, and would catching it on submittal
> day actually be useful?**
>
> If it's a yes and you're open to it, would you let me quote one line from you
> (with your name/title, or anonymised — your call)? Happy to draft something you
> can edit so it takes you 30 seconds. Thanks either way — [Your name]

## C. The "approve-a-quote" follow-up (makes saying yes a 30-second job)

> Thanks [Name]! To make this trivial, here are two drafts — feel free to edit,
> pick one, or write your own:
>
> 1. *"Catching vendor deviations on submittal day instead of in commissioning is
>    exactly where the schedule risk lives. A tool that flags them against the
>    standards the day the document arrives would save us real time and money."*
>    — [Name], [Title], [Company]
>
> 2. *"I've seen a single missed submittal deviation slip a commissioning date by
>    weeks. Surfacing it the day it lands, mapped to the test it'll fail, is the
>    right place to catch it."* — [Name], [Title], [Company]
>
> Even a one-word "yes, accurate" on either is hugely helpful. Anonymised
> ("a commissioning lead at a top-5 India colo") is completely fine if you prefer.

## C2. Discipline-tailored draft quotes (send with C — for a REAL person to approve/edit)

> ⚠️ **Publication rule (non-negotiable):** these are **drafts, not quotes**.
> Nothing below may appear in VALIDATION.md, the README, the deck, the video, or
> any public surface until a **real, identifiable practitioner has approved the
> exact words in writing** (LinkedIn message or email retained off-repo). On
> approval, attribute with *their* real name/title/company (or their chosen
> anonymised form). Publishing an unapproved draft as a quote — or attaching an
> invented name to one — would destroy exactly the evidence-first credibility
> this project runs on, and is plausible disqualification territory.

Tailor the ask: send the draft matching the person's discipline. Each maps to a
capability Pramaan actually demonstrates, so an approver is confirming a pain
they genuinely live.

**For a CxA (controls-integration angle · maps to the BMS/Distech pair + Cx twin):**
> *"In data center EPC projects, L1 submittal reviews are a notorious bottleneck.
> If a vendor changes a sensor location or a BACnet register mapping in a CRAH
> submittal and it gets approved without double-checking the controls integration,
> we don't catch it until L4 functional testing — and it can delay Integrated
> Systems Testing by weeks. Automating the comparison of submittals against the
> Basis of Design to flag these integration and testing risks early is a massive
> win for project schedules."* — [Name], [Title], [Company]

**For a mission-critical MEP PM (power angle · maps to the ATS/switchgear pairs):**
> *"Deviations in vendor submittals for mission-critical power systems — like
> different response times on an automatic transfer switch or breaker rating
> changes — frequently slip through standard document reviews. When these are
> caught late during L5 Integrated Systems Testing, it creates severe
> commissioning and schedule risk. Mapping submittal gaps directly to downstream
> testing impacts is exactly the risk-traceability we need."* — [Name], [Title], [Company]

**For a mechanical/HVAC PE (cooling angle · maps to the STULZ/chiller pairs):**
> *"Vendor submittals for large chillers or CRAH units often carry minor
> discrepancies in fan power, water flow rates, or sound levels against the
> design specification. Reviewing these manually page-by-page is extremely
> time-consuming. Catching a flow-rate deviation at the submittal stage is an
> easy fix; catching it during Level 4 water-loop balancing can delay the entire
> mechanical commissioning schedule."* — [Name], [Title], [Company]

**For a controls/BMS commissioning consultant (integration angle · maps to the ECB-600 pair):**
> *"BMS controls submittals are where data center projects usually get stuck. If
> a chiller vendor submits a controller package with a different register map or
> firmware version than the approved interface spec, it creates immediate
> integration issues. An automated scan of controls submittals that alerts us to
> interface mismatches prevents massive commissioning headaches."* — [Name], [Title], [Company]

**For an EPC project director (schedule/LD angle · maps to the schedule-risk layer):**
> *"In data center EPC projects, schedule is everything. Delayed or incorrect
> submittal reviews lead to late equipment delivery, which directly impacts the
> commissioning timeline and risks liquidated damages. Tracing vendor submittal
> errors directly to downstream testing delays helps project managers prioritise
> which submittals need critical escalation before they hit the field."* — [Name], [Title], [Company]

## D. Email to a warm intro / former colleague

> Subject: 60-sec favour — does this match what you see in commissioning?
>
> Hi [Name], hope you're well. I built a small tool aimed at the spec-vs-submittal
> review problem on data-centre builds — it catches vendor deviations the day the
> submittal lands and maps each one to the commissioning test it'll fail. Two
> questions only: (1) is this a real pain in your experience? (2) if yes, may I
> quote one line from you for the project? I'll draft it so it costs you nothing.
> [Link to /judge demo — optional.] Thanks! — [Your name]

---

## Where the quote goes

Drop the approved line(s) into [`docs/VALIDATION.md §5`](VALIDATION.md) (replacing
the "one thing left" gap) and the README headline. Even one anonymised
practitioner line ("a CxA at a top-5 India colo: 'this is exactly where the risk
lives'") moves the customer-validation dimension from a 3 toward a 7 — the biggest
single score gain available.

## Tracking

| # | Name | Role / company | Channel | Sent | Reply | Quote? |
|---|------|----------------|---------|------|-------|--------|
| 1 |      |                |         |      |       |        |
| 2 |      |                |         |      |       |        |
| 3 |      |                |         |      |       |        |
| 4 |      |                |         |      |       |        |
| 5 |      |                |         |      |       |        |
