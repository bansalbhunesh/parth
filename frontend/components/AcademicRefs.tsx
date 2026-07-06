// All four references verified against their publishers (2026-07-06):
// titles, volumes, and years are as published, each with a resolvable link.
const REFS = [
  {
    title: "Generative AI-Assisted Compliance Checking for Construction Requirements",
    venue: "ASCE J. Constr. Eng. Mgmt., Vol 152 No 8",
    year: 2026,
    url: "https://ascelibrary.org/doi/10.1061/JCEMD4.COENG-18122",
    relevance: "GenAI for automated construction requirement compliance checking — the closest published task to Pramaan's reconcile step",
  },
  {
    title:
      "Leveraging Graph-RAG and Prompt Engineering to Enhance LLM-Based Automated Requirement Traceability and Compliance Checks",
    venue: "arXiv 2412.08593",
    year: 2024,
    url: "https://arxiv.org/abs/2412.08593",
    relevance:
      "Graph-RAG + prompting for requirement traceability and compliance in regulated industries — architectural precedent for Pramaan's graph + retrieval design (cross-domain, not construction-specific)",
  },
  {
    title:
      "Invariant Signature, Logic Reasoning, and Semantic NLP-Based Automated Building Code Compliance Checking (I-SNACC) Framework",
    venue: "J. Information Technology in Construction (ITcon), Vol 28",
    year: 2023,
    url: "https://www.itcon.org/paper/2023/1",
    relevance: "NLP + logic framework for automated code compliance — validates cross-document reasoning approach",
  },
  {
    title: "Identification and Categorization of Defects in Construction Specifications Utilizing Natural Language Processing",
    venue: "ASCE J. Constr. Eng. Mgmt., Vol 152 No 5",
    year: 2026,
    url: "https://ascelibrary.org/doi/10.1061/JCEMD4.COENG-17750",
    relevance: "NLP defect detection in construction specs — directly comparable to Pramaan's extraction stage",
  },
];

export default function AcademicRefs() {
  return (
    <div className="refs">
      {REFS.map((r, i) => (
        <div key={i} className="ref-card">
          <div className="ref-title">{r.title}</div>
          <div className="ref-venue">
            {r.venue} ({r.year}) ·{" "}
            <a href={r.url} target="_blank" rel="noreferrer">
              source ↗
            </a>
          </div>
          <div className="ref-relevance">{r.relevance}</div>
        </div>
      ))}
    </div>
  );
}
