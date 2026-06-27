# Pramaan — Executive Summary (for a non-technical reader)

**One sentence:** Pramaan is an AI that reads a data-centre's design documents and
its equipment vendors' quotes, and flags — on day one — where the vendor is about
to deliver something that doesn't meet spec, before it becomes a multi-million-dollar
construction delay.

## The problem, in plain terms
Building a data centre means buying hundreds of pieces of equipment (UPS, generators,
chillers, switchgear). Each vendor sends a spec sheet. A human has to check every
one against the design and the safety standards. They miss things — not from
carelessness, but because the detail is buried across thousands of pages in three
separate documents. The miss surfaces **months later, during testing**, when it's
the most expensive moment possible to fix: **a single slip on a large build costs
$10–40 million a month** (lost revenue + financing + penalties), and **9 in 10 large
builds run late** (Oxford research).

## What Pramaan does
It reads all three documents together and catches the mismatch **the day the vendor
quote arrives** — when fixing it is a one-line email, not a schedule disaster. For
each issue it says *which test it will fail and how many weeks early you caught it*.

## Why it's believable (not a slide)
We pointed it at **real spec sheets from real vendors** — Vertiv, Cummins, STULZ,
ABB and others — against the real industry standards. It found **15 genuine problems
out of 15, with zero false alarms.** It even did engineering on its own: it divided
a fuel tank by a burn rate to prove a generator couldn't last the required time, and
it knew the environmental rating of a refrigerant the spec sheet never printed. Try
it live: **parth-tan.vercel.app/judge**.

## The business
- **Buyers:** the owner's engineer, the construction contractor, the data-centre
  operator, the commissioning authority — anyone on the hook for the delay.
- **Value:** one prevented slip is worth **$4–25M**; the check costs rupees. That's
  a **10–100× return on a single catch.**
- **Market:** India alone is investing **~$30B toward 2 GW of data centres by 2026**;
  every build does this check by hand today.

## What's proven vs what's next
- **Proven:** works live on real equipment, with a real-world accuracy result, an
  open and reproducible test suite, and a scale benchmark (665 systems/sec). It even
  keeps working when the AI is rate-limited — it never returns a blank.
- **Next:** a paying pilot. The technology and the evidence are ready; we're seeking
  one data-centre owner or EPC to run it on a live submittal package.

*Detail for the technical reader: [`ARCHITECTURE.md`](ARCHITECTURE.md) ·
[`BUSINESS.md`](BUSINESS.md) · [`../eval/REAL_PAIRS_EVAL.md`](../eval/REAL_PAIRS_EVAL.md)*
