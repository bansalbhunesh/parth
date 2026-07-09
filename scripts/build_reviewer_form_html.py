#!/usr/bin/env python3
"""build_reviewer_form_html.py — render the reviewer packet as one HTML form.

Produces reviewer_packet/reviewer_form.html: a self-contained page (no network,
no server — open the file in any browser) holding all 44 labels, the per-pair
owner/vendor context, and exactly the questions from reviewer_instructions.md.
Answers autosave to the browser's localStorage; "Download CSV" emits a file in
the same column layout as reviewer_form.csv, so a returned form imports with
the existing pipeline unchanged:

  python scripts/import_reviewer2_feedback.py --form reviewer_form.<name>.csv

Meant for fan-out to multiple human reviewers: send each person the one HTML
file, get one CSV back per person. Regenerate after any change to
reviewer_form.jsonl or pair_context/:

  python scripts/build_reviewer_form_html.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import benchmark_lib as L  # noqa: E402

PACKET = L.BENCH / "reviewer_packet"
OUT = PACKET / "reviewer_form.html"

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pramaan benchmark — human label review (ps4_external_v1)</title>
<style>
  :root {
    --bg: #f6f7f9; --card: #ffffff; --ink: #1a2233; --muted: #5b6474;
    --line: #d9dee7; --accent: #1f4fd8; --accent-ink: #ffffff;
    --quote: #f0f3f9; --warn: #b45309; --ok: #15803d;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #12151c; --card: #1a1f2a; --ink: #e8ecf4; --muted: #9aa4b5;
      --line: #333c4d; --accent: #7da2ff; --accent-ink: #0e1320;
      --quote: #232a38; --warn: #f59e0b; --ok: #4ade80;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
    font: 15px/1.55 system-ui, "Segoe UI", Roboto, Arial, sans-serif; }
  main { max-width: 880px; margin: 0 auto; padding: 16px 16px 96px; }
  h1 { font-size: 24px; margin: 18px 0 4px; }
  h2 { font-size: 17px; margin: 26px 0 8px; }
  p { margin: 8px 0; }
  .muted { color: var(--muted); }
  .card { background: var(--card); border: 1px solid var(--line);
    border-radius: 10px; padding: 18px 20px; margin: 14px 0; }
  .callout { border-color: var(--accent); background: var(--quote); }
  code, pre { font-family: ui-monospace, Consolas, monospace; font-size: 13px; }
  pre.ctx { background: var(--quote); border: 1px solid var(--line);
    border-radius: 8px; padding: 12px 14px; white-space: pre-wrap;
    overflow-x: auto; max-height: 420px; overflow-y: auto; }
  /* reviewer identity */
  .id-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  @media (max-width: 620px) { .id-grid { grid-template-columns: 1fr; } }
  .field label { display: block; font-weight: 600; font-size: 13px; margin-bottom: 4px; }
  input[type=text], textarea { width: 100%; padding: 8px 10px; border-radius: 7px;
    border: 1px solid var(--line); background: var(--bg); color: var(--ink);
    font: inherit; }
  textarea { min-height: 54px; resize: vertical; }
  input:focus-visible, textarea:focus-visible, button:focus-visible,
  summary:focus-visible, input[type=radio]:focus-visible {
    outline: 3px solid var(--accent); outline-offset: 2px; }
  /* sticky progress */
  .progress-bar { position: sticky; top: 0; z-index: 10; background: var(--card);
    border-bottom: 1px solid var(--line); padding: 8px 16px;
    display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
  .progress-track { flex: 1 1 160px; height: 10px; border-radius: 5px;
    background: var(--quote); overflow: hidden; min-width: 120px; }
  .progress-fill { height: 100%; width: 0%; background: var(--accent);
    transition: width .25s; }
  .progress-text { font-size: 13px; font-variant-numeric: tabular-nums; }
  button { font: inherit; font-weight: 600; border-radius: 8px; cursor: pointer;
    padding: 8px 14px; border: 1px solid var(--line);
    background: var(--card); color: var(--ink); min-height: 40px; }
  button.primary { background: var(--accent); color: var(--accent-ink);
    border-color: var(--accent); }
  button.small { padding: 4px 10px; min-height: 32px; font-size: 13px; }
  /* label cards */
  .label-card { border: 1px solid var(--line); border-radius: 10px;
    background: var(--card); margin: 18px 0; padding: 0; overflow: hidden; }
  .label-head { display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
    padding: 12px 20px; border-bottom: 1px solid var(--line);
    background: var(--quote); }
  .label-head .lid { font-weight: 700; font-family: ui-monospace, Consolas, monospace; }
  .chip { font-size: 12px; padding: 2px 9px; border-radius: 999px;
    border: 1px solid var(--line); color: var(--muted); white-space: nowrap; }
  .done-mark { margin-left: auto; font-size: 13px; color: var(--muted); }
  .done-mark.is-done { color: var(--ok); font-weight: 700; }
  .label-body { padding: 16px 20px; }
  .finding { font-size: 15.5px; font-weight: 600; margin: 0 0 12px; }
  table.vals { border-collapse: collapse; width: 100%; margin: 8px 0 12px;
    font-size: 14px; }
  table.vals th, table.vals td { text-align: left; padding: 6px 10px;
    border: 1px solid var(--line); vertical-align: top; }
  table.vals th { background: var(--quote); font-weight: 600; white-space: nowrap; }
  .evidence { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 10px 0; }
  @media (max-width: 680px) { .evidence { grid-template-columns: 1fr; } }
  .evidence blockquote { margin: 0; background: var(--quote);
    border: 1px solid var(--accent); border-radius: 6px;
    padding: 8px 12px; font-size: 13.5px; }
  .evidence .src { display: block; font-size: 12px; font-weight: 700;
    color: var(--muted); margin-bottom: 4px; text-transform: uppercase;
    letter-spacing: .04em; }
  details { margin: 10px 0; }
  summary { cursor: pointer; font-weight: 600; font-size: 14px;
    padding: 6px 2px; min-height: 32px; }
  /* questions */
  fieldset { border: 1px solid var(--line); border-radius: 8px;
    margin: 12px 0; padding: 10px 14px 12px; }
  legend { font-weight: 700; font-size: 13.5px; padding: 0 6px; }
  .opts { display: flex; flex-wrap: wrap; gap: 4px 14px; }
  .opts label { display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 4px; font-size: 14px; cursor: pointer; min-height: 36px; }
  .opts input[type=radio] { width: 17px; height: 17px; accent-color: var(--accent); }
  .opt-hint { color: var(--muted); font-size: 12.5px; }
  .yn-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
  @media (max-width: 680px) { .yn-row { grid-template-columns: 1fr; } }
  .free-grid { display: grid; gap: 10px; margin-top: 8px; }
  .footer-actions { display: flex; gap: 12px; flex-wrap: wrap; margin: 26px 0; }
  .req-note { color: var(--warn); font-size: 13px; }
  ul { margin: 6px 0; padding-left: 22px; }
  li { margin: 3px 0; }
</style>
</head>
<body>
<div class="progress-bar">
  <span class="progress-text" id="progressText">0 / 0 reviewed</span>
  <div class="progress-track" aria-hidden="true"><div class="progress-fill" id="progressFill"></div></div>
  <button class="small" id="jumpBtn" type="button">Jump to next unanswered</button>
  <button class="small primary" id="exportTopBtn" type="button">Download my CSV</button>
</div>
<main>
  <h1>Human label review — Pramaan EPC deviation benchmark</h1>
  <p class="muted">Benchmark <code>ps4_external_v1</code> · 44 selected ground-truth
    labels · one independent opinion per reviewer</p>

  <div class="card callout">
    <p><strong>You are checking the benchmark's ground-truth labels — not any
    software's output.</strong> For each label below, decide whether the claimed
    deviation (or clean negative) actually holds, using <strong>only</strong> the
    excerpts and pair context shown with it.</p>
    <ul>
      <li>The documents are <strong>team-authored fixtures</strong> modeled on public
        reference values — they are <em>not</em> real vendor datasheets or real submittals.</li>
      <li>If you are unsure, choose <code>contested</code> or
        <code>needs_more_evidence</code>. <strong>Do not force accept/reject —
        honest disagreement is the point.</strong></li>
      <li>Do not judge the product, UI, model quality, or business idea.</li>
      <li>Do not apply values from memory or external standards, <em>unless</em> the
        pair context includes an explicit public-source / provenance note — then you
        may use that cited value to check the derivation.</li>
      <li>Please review <strong>independently</strong>: do not discuss verdicts with
        other reviewers before sending your form back.</li>
    </ul>
    <p>Your answers save automatically in this browser as you type. When done,
    click <strong>Download my CSV</strong> and send the file back.</p>
  </div>

  <div class="card">
    <h2 style="margin-top:0">Who is reviewing?</h2>
    <div class="id-grid">
      <div class="field">
        <label for="revName">Your name <span class="req-note">(required for the export)</span></label>
        <input type="text" id="revName" autocomplete="name" placeholder="e.g. A. Sharma">
      </div>
      <div class="field">
        <label for="revRole">Role / discipline</label>
        <input type="text" id="revRole" placeholder="e.g. electrical engineer, MEP PM, commissioning agent">
      </div>
    </div>
  </div>

  <div class="card">
    <h2 style="margin-top:0">Verdict options (question 1 on every label)</h2>
    <ul>
      <li><code>accept</code> — label is correct and well-evidenced.</li>
      <li><code>accept_with_minor_edit</code> — correct, but a small wording/value tidy would help.</li>
      <li><code>modify</code> — needs a substantive change (say what in "suggested correction").</li>
      <li><code>reject</code> — the label is wrong or unsupported.</li>
      <li><code>contested</code> — genuinely arguable either way.</li>
      <li><code>needs_more_evidence</code> — cannot decide from what is provided.</li>
    </ul>
  </div>

  <div id="cards"></div>

  <div class="footer-actions">
    <button class="primary" id="exportCsvBtn" type="button">Download my CSV</button>
    <button id="exportJsonBtn" type="button">Download JSONL (alternative)</button>
    <button id="clearBtn" type="button">Clear all my answers…</button>
  </div>
  <p class="muted">Self-contained form — nothing you type leaves this page until
  you download the file yourself and send it back.</p>
</main>

<script>
const LABELS = __LABELS_JSON__;
const CONTEXTS = __CONTEXTS_JSON__;
const STORE_KEY = "pramaan-ps4ext-v1-review";
const COLS = ["label_id","pair_id","system_type","label_type","difficulty",
  "component","parameter","required_value","submitted_value","expected_finding",
  "required_evidence_excerpt","submitted_evidence_excerpt","source_basis",
  "commissioning_test","schedule_impact_category","reviewer_verdict",
  "reviewer_confidence","evidence_sufficient_yes_no","severity_ok_yes_no",
  "difficulty_ok_yes_no","commissioning_mapping_ok_yes_no",
  "suggested_correction","missing_related_label","reviewer_notes",
  "reviewer_name","reviewer_role","review_date"];
const VERDICTS = [
  ["accept", "correct and well-evidenced"],
  ["accept_with_minor_edit", "correct, small tidy would help"],
  ["modify", "needs a substantive change"],
  ["reject", "wrong or unsupported"],
  ["contested", "genuinely arguable"],
  ["needs_more_evidence", "cannot decide from what is provided"],
];
const YN_QUESTIONS = [
  ["evidence", "Is the evidence sufficient? (do the excerpts support the label?)"],
  ["severity", "Is the severity / schedule-impact category reasonable?"],
  ["difficulty", "Is the difficulty category reasonable?"],
  ["cx", "Is the commissioning-test mapping reasonable?"],
];
const emptyAnswer = () => ({ verdict:"", confidence:"", evidence:"", severity:"",
  difficulty:"", cx:"", correction:"", missing:"", notes:"" });

let state = { name: "", role: "", answers: {} };
try {
  const saved = JSON.parse(localStorage.getItem(STORE_KEY) || "null");
  if (saved && saved.answers) state = saved;
} catch (e) { /* corrupted save — start fresh */ }
LABELS.forEach(l => { if (!state.answers[l.label_id]) state.answers[l.label_id] = emptyAnswer(); });

const esc = s => (s ?? "").toString()
  .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
  .replace(/"/g,"&quot;");

function radioGroup(lid, field, options, allowNA) {
  const name = `${lid}::${field}`;
  let h = "";
  for (const [val, hint] of options) {
    h += `<label><input type="radio" name="${esc(name)}" value="${esc(val)}"` +
      ` data-lid="${esc(lid)}" data-field="${esc(field)}">` +
      `<span>${esc(val)}${hint ? ` <span class="opt-hint">— ${esc(hint)}</span>` : ""}</span></label>`;
  }
  if (allowNA) {
    h += `<label><input type="radio" name="${esc(name)}" value=""` +
      ` data-lid="${esc(lid)}" data-field="${esc(field)}">` +
      `<span>n/a <span class="opt-hint">— leave blank</span></span></label>`;
  }
  return `<div class="opts">${h}</div>`;
}

function renderCard(l, i) {
  const ctx = CONTEXTS[l.pair_id];
  return `<section class="label-card" id="card-${esc(l.label_id)}" aria-label="Label ${esc(l.label_id)}">
  <div class="label-head">
    <span class="lid">${i + 1}. ${esc(l.label_id)}</span>
    <span class="chip">${esc(l.pair_id)}</span>
    <span class="chip">${esc(l.system_type)}</span>
    <span class="chip">${esc(l.label_type)}</span>
    <span class="chip">${esc(l.difficulty)}</span>
    <span class="done-mark" id="done-${esc(l.label_id)}">unanswered</span>
  </div>
  <div class="label-body">
    <p class="finding">${esc(l.expected_finding)}</p>
    <table class="vals">
      <tr><th scope="row">Component</th><td>${esc(l.component)}</td>
          <th scope="row">Parameter</th><td>${esc(l.parameter)}</td></tr>
      <tr><th scope="row">Required value</th><td>${esc(l.required_value)}</td>
          <th scope="row">Submitted value</th><td>${esc(l.submitted_value)}</td></tr>
      <tr><th scope="row">Commissioning test</th><td>${esc(l.commissioning_test)}</td>
          <th scope="row">Schedule impact</th><td>${esc(l.schedule_impact_category)}</td></tr>
      <tr><th scope="row">Source basis</th><td colspan="3">${esc(l.source_basis)}</td></tr>
    </table>
    <div class="evidence">
      <blockquote><span class="src">Required-value evidence</span>${esc(l.required_evidence_excerpt)}</blockquote>
      <blockquote><span class="src">Submitted-value evidence</span>${esc(l.submitted_evidence_excerpt)}</blockquote>
    </div>
    ${ctx ? `<details><summary>Full pair context (owner requirement + vendor submittal${
        /[Pp]rovenance/.test(ctx) ? " + provenance" : ""
      })</summary><pre class="ctx">${esc(ctx)}</pre></details>` : ""}
    <fieldset>
      <legend>1. Verdict — is this label valid?</legend>
      ${radioGroup(l.label_id, "verdict", VERDICTS, false)}
    </fieldset>
    <fieldset>
      <legend>2. Your confidence in that verdict</legend>
      ${radioGroup(l.label_id, "confidence", [["high",""],["medium",""],["low",""]], false)}
    </fieldset>
    <div class="yn-row">
      ${YN_QUESTIONS.map(([f, q], qi) => `<fieldset>
        <legend>${qi + 3}. ${esc(q)}</legend>
        ${radioGroup(l.label_id, f, [["yes",""],["no",""]], true)}
      </fieldset>`).join("")}
    </div>
    <div class="free-grid">
      <div class="field">
        <label for="corr-${esc(l.label_id)}">7. Suggested correction
          <span class="opt-hint">(required if you chose modify)</span></label>
        <textarea id="corr-${esc(l.label_id)}" data-lid="${esc(l.label_id)}" data-field="correction"></textarea>
      </div>
      <div class="field">
        <label for="miss-${esc(l.label_id)}">8. Missing label in the same pair?
          <span class="opt-hint">(a deviation the benchmark did not capture —
          leave blank if none)</span></label>
        <textarea id="miss-${esc(l.label_id)}" data-lid="${esc(l.label_id)}" data-field="missing"></textarea>
      </div>
      <div class="field">
        <label for="note-${esc(l.label_id)}">9. Notes
          <span class="opt-hint">(anything else — ambiguity, wording, unit
          concerns)</span></label>
        <textarea id="note-${esc(l.label_id)}" data-lid="${esc(l.label_id)}" data-field="notes"></textarea>
      </div>
    </div>
  </div>
</section>`;
}

document.getElementById("cards").innerHTML = LABELS.map(renderCard).join("");

// --- restore saved state into the DOM ---
document.getElementById("revName").value = state.name || "";
document.getElementById("revRole").value = state.role || "";
for (const l of LABELS) {
  const a = state.answers[l.label_id];
  for (const [field, val] of Object.entries(a)) {
    if (["correction","missing","notes"].includes(field)) {
      const el = document.querySelector(`textarea[data-lid="${CSS.escape(l.label_id)}"][data-field="${field}"]`);
      if (el) el.value = val;
    } else if (val !== "") {
      const sel = `input[name="${CSS.escape(l.label_id + "::" + field)}"]` +
        `[value="${CSS.escape(val)}"]`;
      const el = document.querySelector(sel);
      if (el) el.checked = true;
    }
  }
}

function save() { localStorage.setItem(STORE_KEY, JSON.stringify(state)); }

function updateProgress() {
  const total = LABELS.length;
  const done = LABELS.filter(l => state.answers[l.label_id].verdict !== "").length;
  document.getElementById("progressText").textContent = `${done} / ${total} reviewed`;
  document.getElementById("progressFill").style.width = (100 * done / total) + "%";
  for (const l of LABELS) {
    const el = document.getElementById(`done-${l.label_id}`);
    const isDone = state.answers[l.label_id].verdict !== "";
    el.textContent = isDone ? "\\u2713 answered" : "unanswered";
    el.classList.toggle("is-done", isDone);
  }
}

document.body.addEventListener("input", e => {
  const t = e.target;
  if (t.id === "revName") state.name = t.value;
  else if (t.id === "revRole") state.role = t.value;
  else if (t.dataset && t.dataset.lid) state.answers[t.dataset.lid][t.dataset.field] = t.value;
  else return;
  save(); updateProgress();
});

document.getElementById("jumpBtn").addEventListener("click", () => {
  const next = LABELS.find(l => state.answers[l.label_id].verdict === "");
  if (!next) {
    document.getElementById("progressText").textContent =
      "All " + LABELS.length + " reviewed \\u2713";
    return;
  }
  document.getElementById("card-" + next.label_id).scrollIntoView({ behavior: "smooth", block: "start" });
});

// --- export ---
const csvField = v => /[",\\n\\r]/.test(v = (v ?? "").toString()) ? '"' + v.replace(/"/g, '""') + '"' : v;
const slug = s => (s || "unnamed").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "unnamed";
const today = () => new Date().toISOString().slice(0, 10);

function rowFor(l) {
  const a = state.answers[l.label_id];
  return {
    ...l,
    reviewer_verdict: a.verdict, reviewer_confidence: a.confidence,
    evidence_sufficient_yes_no: a.evidence, severity_ok_yes_no: a.severity,
    difficulty_ok_yes_no: a.difficulty, commissioning_mapping_ok_yes_no: a.cx,
    suggested_correction: a.correction, missing_related_label: a.missing,
    reviewer_notes: a.notes,
    reviewer_name: state.name.trim(), reviewer_role: state.role.trim(),
    review_date: today(),
  };
}

function preflight() {
  if (!state.name.trim()) {
    alert("Please enter your name first (top of the page) so the export file identifies you.");
    document.getElementById("revName").focus();
    return false;
  }
  const missing = LABELS.filter(l => state.answers[l.label_id].verdict === "").length;
  const needCorr = LABELS.filter(l => state.answers[l.label_id].verdict === "modify"
    && !state.answers[l.label_id].correction.trim()).map(l => l.label_id);
  let msg = "";
  if (missing) msg += missing + " of " + LABELS.length + " labels still have no verdict.\\n";
  if (needCorr.length) msg += "These have verdict=modify but no suggested correction: " + needCorr.join(", ") + "\\n";
  return !msg || confirm(msg + "\\nDownload anyway?");
}

function download(name, text, type) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  a.click();
  URL.revokeObjectURL(a.href);
}

function exportCsv() {
  if (!preflight()) return;
  const lines = [COLS.join(",")];
  for (const l of LABELS) {
    const r = rowFor(l);
    lines.push(COLS.map(c => csvField(r[c])).join(","));
  }
  download("reviewer_form." + slug(state.name) + ".csv", lines.join("\\r\\n") + "\\r\\n", "text/csv");
}

function exportJsonl() {
  if (!preflight()) return;
  const text = LABELS.map(l => JSON.stringify(rowFor(l))).join("\\n") + "\\n";
  download("reviewer_form." + slug(state.name) + ".jsonl", text, "application/json");
}

document.getElementById("exportCsvBtn").addEventListener("click", exportCsv);
document.getElementById("exportTopBtn").addEventListener("click", exportCsv);
document.getElementById("exportJsonBtn").addEventListener("click", exportJsonl);
document.getElementById("clearBtn").addEventListener("click", () => {
  if (!confirm("Erase everything you have entered in this form on this browser? This cannot be undone.")) return;
  localStorage.removeItem(STORE_KEY);
  location.reload();
});

updateProgress();
</script>
</body>
</html>
"""


def main() -> int:
    labels = [json.loads(line) for line in
              (PACKET / "reviewer_form.jsonl").read_text(encoding="utf-8").splitlines()
              if line.strip()]
    # drop the empty answer columns from the embedded context; answers live in JS state
    ctx_labels = [{k: v for k, v in rec.items()
                   if not (k.startswith("reviewer_") or k.endswith("_yes_no")
                           or k in ("suggested_correction", "missing_related_label"))}
                  for rec in labels]
    contexts = {p.stem.removesuffix("_context"): p.read_text(encoding="utf-8")
                for p in sorted((PACKET / "pair_context").glob("*_context.md"))}
    used = {rec["pair_id"] for rec in ctx_labels}
    contexts = {k: v for k, v in contexts.items() if k in used}

    def embed(obj) -> str:
        # </script>-safe JSON for inline embedding
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    html = (TEMPLATE
            .replace("__LABELS_JSON__", embed(ctx_labels))
            .replace("__CONTEXTS_JSON__", embed(contexts)))
    OUT.write_text(html, encoding="utf-8")
    missing_ctx = sorted(used - set(contexts))
    print(f"wrote {OUT.relative_to(L.BENCH.parent.parent)} "
          f"({len(ctx_labels)} labels, {len(contexts)} pair contexts, "
          f"{OUT.stat().st_size / 1024:.0f} KB)")
    if missing_ctx:
        print(f"[!] no pair_context file for: {', '.join(missing_ctx)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
