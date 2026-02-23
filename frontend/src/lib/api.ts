import type {
  ChatRequest,
  ChatResponse,
  CompareResponse,
  IngestionResult,
  SystemStatus,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

// ---- Chat ----
export async function sendChat(req: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>("/api/v1/chat", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function sendCompare(
  req: ChatRequest
): Promise<CompareResponse> {
  return request<CompareResponse>("/api/v1/compare", {
    method: "POST",
    body: JSON.stringify({ ...req, mode: "compare" }),
  });
}

// ---- Ingestion ----
export async function triggerIngestion(
  source: string = "all",
  forceRefresh: boolean = false
): Promise<IngestionResult> {
  return request<IngestionResult>("/api/v1/ingest", {
    method: "POST",
    body: JSON.stringify({ source, force_refresh: forceRefresh }),
  });
}

// ---- Status ----
export async function getSystemStatus(): Promise<SystemStatus> {
  return request<SystemStatus>("/api/v1/status");
}

// ---- Evaluation ----
export async function runEvaluation(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/api/v1/evaluate");
}

// ---- Namespaces ----
export async function getNamespaces(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/api/v1/namespaces");
}
