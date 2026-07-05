const REFS = [
  {
    title: "Generative AI-Assisted Compliance Checking for Construction Requirements",
    venue: "ASCE J. Constr. Eng. Mgmt., Vol 152 No 8",
    year: 2024,
    relevance: "GenAI for automated construction compliance checking; benchmark of 100 scenarios",
  },
  {
    title: "Graph-RAG for Construction Compliance",
    venue: "arXiv 2412.08593",
    year: 2024,
    relevance: "Hybrid knowledge graph + RAG for regulatory compliance — architectural precedent for Pramaan",
  },
  {
    title: "I-SNACC: Invariant Signature, Logic Reasoning, and Semantic NLP-Based Automated Building Code Compliance",
    venue: "J. IT in Construction",
    year: 2023,
    relevance: "NLP framework for automated code compliance — validates cross-document reasoning approach",
  },
  {
    title: "Identification and Categorization of Defects in Construction Specifications Utilizing NLP",
    venue: "ASCE JCEM Vol 152 No 5",
    year: 2026,
    relevance: "NLP defect detection in construction specs — directly comparable to Pramaan's extraction stage",
  },
];

export default function AcademicRefs() {
  return (
    <div className="refs">
      {REFS.map((r, i) => (
        <div key={i} className="ref-card">
          <div className="ref-title">{r.title}</div>
          <div className="ref-venue">{r.venue} ({r.year})</div>
          <div className="ref-relevance">{r.relevance}</div>
        </div>
      ))}
    </div>
  );
}
