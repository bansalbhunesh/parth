"use client";
import { useState } from "react";

interface Props {
  caseId?: string;
  caseSecret?: string;
}

export default function ItpExportButton({ caseId: initialCaseId, caseSecret: initialSecret }: Props) {
  const [loading, setLoading] = useState(false);

  async function handleDownload() {
    let caseId = initialCaseId;
    let caseSecret = initialSecret;
    if (!caseId) {
      caseId = window.prompt("Enter Case ID to export ITP:") || "";
      if (!caseId) return;
    }
    if (!caseSecret) {
      caseSecret = window.prompt("Enter Case Secret:") || "";
      if (!caseSecret) return;
    }

    setLoading(true);
    try {
      const api = process.env.NEXT_PUBLIC_API ?? "http://127.0.0.1:8000";
      const res = await fetch(
        `${api}/cases/${caseId}/export/itp.pdf`,
        { headers: { "X-Case-Secret": caseSecret } },
      );
      if (!res.ok) throw new Error(`${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `itp_${caseId.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Failed to export ITP. Check Case ID and Secret.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <button
      id="itp-export-btn"
      onClick={handleDownload}
      disabled={loading}
      className="export-btn itp-export-btn"
      title="Download Inspection & Test Plan as PDF"
    >
      {loading ? "Generating…" : "⬇ ITP PDF"}
    </button>
  );
}
