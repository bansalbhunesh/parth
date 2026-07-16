import type {
  BlastRadius,
  CopilotResponse,
  CxPlan,
  Deviation,
  HealthStatus,
  MultiProjectEval,
  OcrStatus,
  ProjectGraph,
  ProjectSummary,
  RegisterProvenanceKind,
  RegisterSnapshot,
  RemediationSim,
  ScheduleAnalysis,
  SupplyChainAnalysis,
  UploadExtraction,
} from "./api-types";
import {
  FALLBACK,
  FALLBACK_CX_PLAN,
  FALLBACK_GRAPH,
  FALLBACK_MULTI_EVAL,
  FALLBACK_PROJECTS,
  FALLBACK_REMEDIATION,
  FALLBACK_SCHEDULE,
  FALLBACK_SUPPLY,
} from "./api-fallbacks";

export type * from "./api-types";
export * from "./api-fallbacks";

const API = process.env.NEXT_PUBLIC_API ?? "http://127.0.0.1:8000";

export function apiUrl(path: string): string {
  return `${API}${path}`;
}

// Time-box server-rendered data fetches. A cold Render free-tier backend can
// take 30s+ to wake; without a timeout the page render blocks on it. With one,
// we render instantly from the bundled fallback data if the API is slow.
const FETCH_TIMEOUT_MS = 2500;

function fetchOpts(opts: RequestInit = {}): RequestInit {
  try {
    return { ...opts, signal: AbortSignal.timeout(FETCH_TIMEOUT_MS) };
  } catch {
    return opts; // AbortSignal.timeout unavailable (very old runtime) — skip
  }
}


async function consumeSSE(
  response: Response,
  handlers: Record<string, (data: string) => void>,
  signal?: AbortSignal,
): Promise<void> {
  if (!response.body) return;
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";

  try {
    while (true) {
      if (signal?.aborted) throw new DOMException("Analysis cancelled", "AbortError");
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("event: ")) {
          currentEvent = line.slice(7).trim();
        } else if (line.startsWith("data: ")) {
          const handler = handlers[currentEvent];
          if (handler) handler(line.slice(6));
        }
      }
    }
  } finally {
    if (signal?.aborted) await reader.cancel().catch(() => undefined);
  }
}


export async function getRegisterSnapshot(): Promise<RegisterSnapshot> {
  try {
    // Cacheable so the page can be ISR-rendered (instant reloads); refreshed
    // in the background every 10 min. Timeout still guards the background fetch.
    const r = await fetch(`${API}/deviations`, fetchOpts({ next: { revalidate: 600 } }));
    if (!r.ok) throw new Error(String(r.status));
    const data = await r.json();
    if (!Array.isArray(data.register)) throw new Error("invalid register payload");
    const rawProvenance = data.provenance ?? {};
    const kind: RegisterProvenanceKind = rawProvenance.kind === "deterministic"
      ? "deterministic"
      : data.analysis_mode === "pipeline" || data.analysis_mode === "llm"
        ? "live"
        : data.analysis_mode === "unavailable"
          ? "unavailable"
          : "cached";
    return {
      rows: data.register as Deviation[],
      analysisMode: String(data.analysis_mode ?? "unknown"),
      provenance: {
        kind,
        label: String(rawProvenance.label ?? "Project register"),
        description: String(
          rawProvenance.description
            ?? "Loaded from the configured Pramaan analysis API.",
        ),
        live: rawProvenance.live === true,
        sourceDocuments: typeof rawProvenance.source_documents === "number"
          ? rawProvenance.source_documents
          : undefined,
      },
    };
  } catch {
    return {
      rows: FALLBACK,
      analysisMode: "bundled_reference",
      provenance: {
        kind: "bundled_reference",
        label: "Bundled reference snapshot",
        description:
          "The analysis API did not respond within 2.5 seconds. These labelled reference findings keep the walkthrough available; they are not live inference.",
        live: false,
        sourceDocuments: 20,
      },
    };
  }
}

export async function getRegister(): Promise<Deviation[]> {
  return (await getRegisterSnapshot()).rows;
}

export async function getCxPlan(): Promise<CxPlan | null> {
  try {
    const r = await fetch(`${API}/cx-plan`, fetchOpts({ next: { revalidate: 600 } }));
    if (!r.ok) throw new Error(String(r.status));
    const data = await r.json();
    // The backend returns {} (HTTP 200) when cx_plan.json is missing/unparseable.
    // An empty object is truthy, so without this guard CommissioningTwin would
    // render and throw on Object.entries(undefined) / cxPlan.tests.map — and the
    // top-level ErrorBoundary would blank the whole dashboard. Treat a shape-
    // invalid payload as a failure and use the bundled fallback instead.
    if (!data || !data.levels || !data.tests) return FALLBACK_CX_PLAN;
    return data as CxPlan;
  } catch {
    return FALLBACK_CX_PLAN;
  }
}

// ── PS4 capability layers: schedule risk · supply chain · project graph ──────

export async function getRemediation(devId = "DEV-001", projectId = "meghdoot"): Promise<RemediationSim> {
  try {
    const r = await fetch(`${API}/projects/${projectId}/remediation/${devId}`, fetchOpts({ next: { revalidate: 600 } }));
    if (!r.ok) throw new Error(String(r.status));
    const d = await r.json();
    if (!d || d.available === false || !Array.isArray(d.curve) || !d.scenarios) {
      return FALLBACK_REMEDIATION;
    }
    return d as RemediationSim;
  } catch {
    return FALLBACK_REMEDIATION;
  }
}

export async function getSchedule(projectId = "meghdoot"): Promise<ScheduleAnalysis> {
  try {
    const r = await fetch(`${API}/projects/${projectId}/schedule`, fetchOpts({ next: { revalidate: 600 } }));
    if (!r.ok) throw new Error(String(r.status));
    const d = await r.json();
    if (!d || d.available === false || !d.monte_carlo || !d.baseline
        || !d.cpm || !d.cpm.tasks || !Array.isArray(d.monte_carlo.histogram)) {
      return FALLBACK_SCHEDULE;
    }
    return d as ScheduleAnalysis;
  } catch {
    return FALLBACK_SCHEDULE;
  }
}

export async function getSupplyChain(projectId = "meghdoot"): Promise<SupplyChainAnalysis> {
  try {
    const r = await fetch(`${API}/projects/${projectId}/supply-chain`, fetchOpts({ next: { revalidate: 600 } }));
    if (!r.ok) throw new Error(String(r.status));
    const d = await r.json();
    if (!d || d.available === false || !d.summary || !Array.isArray(d.shipments)) {
      return FALLBACK_SUPPLY;
    }
    return d as SupplyChainAnalysis;
  } catch {
    return FALLBACK_SUPPLY;
  }
}

export async function getProjectGraph(projectId = "meghdoot"): Promise<ProjectGraph> {
  try {
    const r = await fetch(`${API}/projects/${projectId}/graph`, fetchOpts({ next: { revalidate: 600 } }));
    if (!r.ok) throw new Error(String(r.status));
    const d = await r.json();
    if (!d || d.available === false || !d.graph || !d.stats
        || !Array.isArray(d.graph.nodes) || !Array.isArray(d.graph.edges)) {
      return FALLBACK_GRAPH;
    }
    return d as ProjectGraph;
  } catch {
    return FALLBACK_GRAPH;
  }
}

export async function getBlastRadius(devId: string, projectId = "meghdoot"): Promise<BlastRadius | null> {
  try {
    const r = await fetch(`${API}/projects/${projectId}/blast-radius/${devId}`, { cache: "no-store" });
    if (!r.ok) throw new Error(String(r.status));
    const d = await r.json();
    if (!d || d.available === false) return null;
    return d as BlastRadius;
  } catch {
    return null;
  }
}

export async function askCopilot(query: string): Promise<CopilotResponse> {
  try {
    const r = await fetch(`${API}/copilot`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
      cache: "no-store",
    });
    if (!r.ok) throw new Error(String(r.status));
    return await r.json();
  } catch {
    return {
      answer: "Backend not connected. In production, the copilot searches across all project documents (specs, submittals, standards, RFI log) and returns cited answers with prior-RFI matching.",
      sources: [],
      prior_rfis: [],
    };
  }
}

export async function streamCopilot(
  query: string,
  onMeta: (meta: { sources: string[]; prior_rfis: CopilotResponse["prior_rfis"] }) => void,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
): Promise<void> {
  try {
    const r = await fetch(`${API}/copilot/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);

    await consumeSSE(r, {
      meta: (data) => { try { onMeta(JSON.parse(data)); } catch {} },
      token: (data) => { try { onToken(JSON.parse(data)); } catch { onToken(data); } },
      done: () => { onDone(); },
    });
    onDone();
  } catch {
    onError("Backend not connected. Ensure the API is running at 127.0.0.1:8000.");
  }
}

export async function streamAnalyze(
  specText: string,
  submittalText: string,
  onStatus: (status: string) => void,
  onToken: (token: string) => void,
  onResult: (result: unknown) => void,
  onDone: () => void,
  onError: (err: string) => void,
  signal?: AbortSignal,
  systemId = "CUSTOM",
): Promise<void> {
  try {
    const r = await fetch(`${API}/analyze/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ spec_text: specText, submittal_text: submittalText, system_id: systemId }),
      signal,
    });
    if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);

    await consumeSSE(r, {
      status: (data) => onStatus(data),
      token: (data) => { try { onToken(JSON.parse(data)); } catch { onToken(data); } },
      result: (data) => { try { onResult(JSON.parse(data)); } catch {} },
      done: () => undefined,
    }, signal);
    onDone();
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      onError("Analysis cancelled.");
    } else {
      onError(error instanceof Error ? error.message : "Analysis failed — backend not connected.");
    }
  }
}

export async function streamUploadAnalyze(
  formData: FormData,
  handlers: {
    onStatus: (status: string) => void;
    onPreview: (preview: { spec: string; submittal: string }) => void;
    onExtraction?: (extraction: UploadExtraction) => void;
    onToken: (token: string) => void;
    onResult: (result: unknown) => void;
    onError: (err: string) => void;
    onDone: () => void;
  },
  signal?: AbortSignal,
): Promise<void> {
  try {
    const r = await fetch(`${API}/analyze/upload/stream`, {
      method: "POST",
      body: formData,
      signal,
    });
    if (!r.ok || !r.body) throw new Error(`HTTP ${r.status}`);

    await consumeSSE(r, {
      status: (data) => handlers.onStatus(data),
      preview: (data) => { try { handlers.onPreview(JSON.parse(data)); } catch {} },
      extraction: (data) => { try { handlers.onExtraction?.(JSON.parse(data)); } catch {} },
      token: (data) => {
        try { handlers.onToken(JSON.parse(data)); } catch { handlers.onToken(data); }
      },
      result: (data) => { try { handlers.onResult(JSON.parse(data)); } catch {} },
      error: (data) => handlers.onError(data),
      done: () => undefined,
    }, signal);
    handlers.onDone();
  } catch (e) {
    handlers.onError(
      e instanceof DOMException && e.name === "AbortError"
        ? "Analysis cancelled."
        : e instanceof Error ? e.message : "Upload failed",
    );
  }
}

export async function analyzeOnce<T>(
  specText: string,
  submittalText: string,
  systemId: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${API}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ spec_text: specText, submittal_text: submittalText, system_id: systemId }),
    signal,
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(String(body.detail || `Analysis failed (${response.status})`));
  }
  return body as T;
}

export async function getMetrics(): Promise<Record<string, unknown> | null> {
  try {
    const r = await fetch(`${API}/metrics`, fetchOpts({ cache: "no-store" }));
    if (!r.ok) throw new Error(String(r.status));
    return await r.json();
  } catch {
    return null;
  }
}

export async function getOcrCheck(): Promise<OcrStatus | null> {
  try {
    const r = await fetch(`${API}/ocr-check`, fetchOpts({ cache: "no-store" }));
    if (!r.ok) throw new Error(String(r.status));
    return (await r.json()) as OcrStatus;
  } catch {
    return null;
  }
}

// Live deployment status for the evidence page. Returns null if the backend is
// unreachable — the caller must then say "live status unavailable" rather than
// imply anything is green. Never contains a secret (backend returns booleans/caps).
export async function getHealth(): Promise<HealthStatus | null> {
  try {
    const r = await fetch(`${API}/health`, fetchOpts({ cache: "no-store" }));
    if (!r.ok) throw new Error(String(r.status));
    return (await r.json()) as HealthStatus;
  } catch {
    return null;
  }
}

export async function getProjects(): Promise<ProjectSummary[]> {
  try {
    const r = await fetch(`${API}/projects`, fetchOpts({ cache: "no-store" }));
    if (!r.ok) throw new Error(String(r.status));
    const data = await r.json();
    return data.projects as ProjectSummary[];
  } catch {
    return FALLBACK_PROJECTS;
  }
}

export async function getMultiProjectEval(): Promise<MultiProjectEval | null> {
  try {
    const r = await fetch(`${API}/projects/eval/aggregate`, fetchOpts({ cache: "no-store" }));
    if (!r.ok) throw new Error(String(r.status));
    const data = await r.json();
    // A degraded backend returns {aggregate:{}, error:...} with HTTP 200 — treat
    // that as a miss so the dashboard shows the bundled fallback, not NaN.
    if (!data || typeof data.aggregate?.aggregate_f1 !== "number") return FALLBACK_MULTI_EVAL;
    return data;
  } catch {
    return FALLBACK_MULTI_EVAL;
  }
}
