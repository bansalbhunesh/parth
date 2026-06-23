"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API ?? "http://localhost:8000";

export default function ExportButton() {
  const [loading, setLoading] = useState(false);

  async function handleExport() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/export/audit/html`);
      if (!r.ok) throw new Error("Export failed");
      const html = await r.text();
      const blob = new Blob([html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pramaan-evidence-pack.html";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Export failed. Ensure the backend is running at localhost:8000.");
    }
    setLoading(false);
  }

  return (
    <button className="export-btn" onClick={handleExport} disabled={loading}>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 1v9M4 7l4 4 4-4M2 13h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
      {loading ? "Generating..." : "Export Evidence Pack"}
    </button>
  );
}
