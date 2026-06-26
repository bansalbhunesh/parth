"use client";

const SECTIONS = [
  { id: "sentinel", num: "01", label: "Deviation Sentinel", desc: "Critical UPS finding caught 27 weeks early", color: "#ff4d4d" },
  { id: "workflow", num: "02", label: "Before vs After", desc: "Manual review vs Pramaan — 10 weeks vs 2 minutes", color: "#ffb020" },
  { id: "pipeline", num: "03", label: "Agent Pipeline", desc: "5 AI agents in LangGraph orchestration", color: "#ffb020" },
  { id: "architecture", num: "04", label: "Architecture", desc: "4-layer system design with data flow", color: "#5b8cff" },
  { id: "screenshots", num: "05", label: "Live Screenshots", desc: "Interactive gallery of all dashboard views", color: "#36d6e7" },
  { id: "systems", num: "06", label: "System Health", desc: "10 systems — 3 compliant, 7 with findings", color: "#35c98b" },
  { id: "compliance", num: "07", label: "Compliance Score", desc: "Animated ring gauge with per-system conformance", color: "#35c98b" },
  { id: "diff", num: "08", label: "Document Diff", desc: "Side-by-side spec vs submittal with deviation highlights", color: "#ffb020" },
  { id: "risk", num: "09", label: "Risk Matrix", desc: "Severity x lead time deviation mapping", color: "#ff4d4d" },
  { id: "register", num: "10", label: "Deviation Register", desc: "Full evidence table with citation chains", color: "#ff4d4d" },
  { id: "twin", num: "11", label: "Cx Risk Twin", desc: "Commissioning timeline with at-risk tests", color: "#5b8cff" },
  { id: "standards", num: "12", label: "Standards KB", desc: "7 governing standards with 1,580 lines", color: "#5b8cff" },
  { id: "multiproject", num: "13", label: "Multi-Project Eval", desc: "12 projects, 11 countries, 50 deviations, F1=1.000", color: "#a855f7" },
  { id: "eval", num: "14", label: "Eval Harness", desc: "P/R/F1 = 1.000 with FP rate testing", color: "#35c98b" },
  { id: "roi", num: "15", label: "ROI Calculator", desc: "Interactive business impact model", color: "#ffb020" },
  { id: "scale", num: "16", label: "Scale Story", desc: "10 systems today, 14,000 line items tomorrow", color: "#36d6e7" },
  { id: "analyze", num: "17", label: "Live Analysis", desc: "Upload PDFs or paste text for end-to-end deviation detection", color: "#36d6e7" },
  { id: "copilot", num: "18", label: "Project Copilot", desc: "RAG over specs, submittals, standards & RFIs", color: "#36d6e7" },
  { id: "refs", num: "19", label: "Academic Refs", desc: "Peer-reviewed foundations for the approach", color: "#5b8cff" },
];

export default function SectionIndex() {
  return (
    <div className="sidx">
      <div className="sidx-header">
        <div className="sidx-badge">PRODUCT WALKTHROUGH</div>
        <div className="sidx-title">19 sections &middot; everything a judge needs</div>
      </div>
      <div className="sidx-grid">
        {SECTIONS.map((s) => (
          <a key={s.id} href={`#${s.id}`} className="sidx-item">
            <div className="sidx-num" style={{ color: s.color }}>{s.num}</div>
            <div className="sidx-content">
              <div className="sidx-label">{s.label}</div>
              <div className="sidx-desc">{s.desc}</div>
            </div>
            <svg className="sidx-arrow" width="12" height="12" viewBox="0 0 12 12"><path d="M4 2L8 6L4 10" stroke="currentColor" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </a>
        ))}
      </div>
    </div>
  );
}
