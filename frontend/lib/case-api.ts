import { apiUrl } from "./api";

export interface CaseCredentials {
  caseId: string;
  secret: string;
}

export interface PersistedFindingInput {
  component: string;
  parameter: string;
  required_value: string;
  provided_value: string;
  unit: string;
  severity: string;
  standard_ref: string;
  spec_clause: string;
  predicted_cx_test: string;
  lead_time_weeks: number | null;
  rationale: string;
}

async function requestJson<T>(path: string, init: RequestInit = {}, timeoutMs = 20_000): Promise<T> {
  const timeout = AbortSignal.timeout(timeoutMs);
  const response = await fetch(apiUrl(path), {
    ...init,
    signal: init.signal ? AbortSignal.any([init.signal, timeout]) : timeout,
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(String(body.detail || `Request failed (${response.status})`));
  }
  return body as T;
}

function caseHeaders(secret: string): HeadersInit {
  return { "X-Case-Secret": secret };
}

export async function createCase(name: string): Promise<CaseCredentials> {
  const body = await requestJson<{ case_id: string; secret: string }>("/cases", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  return { caseId: body.case_id, secret: body.secret };
}

export async function addFinding(
  credentials: CaseCredentials,
  finding: PersistedFindingInput,
): Promise<string> {
  const body = await requestJson<{ finding_id: string }>(`/cases/${credentials.caseId}/findings`, {
    method: "POST",
    headers: caseHeaders(credentials.secret),
    body: JSON.stringify(finding),
  });
  return body.finding_id;
}

export async function updateFinding(
  credentials: CaseCredentials,
  findingId: string,
  update: { status?: string; owner?: string; resolution_note?: string },
): Promise<void> {
  await requestJson(`/cases/${credentials.caseId}/findings/${findingId}`, {
    method: "PATCH",
    headers: caseHeaders(credentials.secret),
    body: JSON.stringify(update),
  });
}

export async function draftAndIssueRfi(
  credentials: CaseCredentials,
  findingId: string,
): Promise<string> {
  const drafted = await requestJson<{ rfi_id: string }>(
    `/cases/${credentials.caseId}/findings/${findingId}/rfi`,
    { method: "POST", headers: caseHeaders(credentials.secret) },
    45_000,
  );
  await updateRfi(credentials, drafted.rfi_id, { status: "issued" });
  return drafted.rfi_id;
}

export async function updateRfi(
  credentials: CaseCredentials,
  rfiId: string,
  update: { status: string; response_text?: string },
): Promise<void> {
  await requestJson(`/cases/${credentials.caseId}/rfis/${rfiId}`, {
    method: "PATCH",
    headers: caseHeaders(credentials.secret),
    body: JSON.stringify(update),
  });
}

export async function getAuditCount(credentials: CaseCredentials): Promise<number> {
  const body = await requestJson<{ audit_log: unknown[] }>(`/cases/${credentials.caseId}/audit-log`, {
    headers: caseHeaders(credentials.secret),
  });
  return body.audit_log.length;
}

export async function deleteCase(credentials: CaseCredentials): Promise<void> {
  await requestJson(`/cases/${credentials.caseId}`, {
    method: "DELETE",
    headers: caseHeaders(credentials.secret),
  });
}
