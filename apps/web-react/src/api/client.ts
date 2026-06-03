import type {
  ApiValidationIssue,
  DocumentSummary,
  IngestionResponse,
  RagAnswerResponse,
  TextIngestionPayload,
  TextQueryPayload,
} from "../types";

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function parseApiError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item: ApiValidationIssue) => item.msg ?? JSON.stringify(item))
        .join("; ");
    }
    return JSON.stringify(payload);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return response.json() as Promise<T>;
}

export async function checkHealth(): Promise<void> {
  await fetchJson<{ status: string }>("/health");
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  const payload = await fetchJson<{ documents: DocumentSummary[] }>("/api/documents");
  return payload.documents;
}

export async function uploadDocument(formData: FormData): Promise<IngestionResponse> {
  return fetchJson<IngestionResponse>("/api/ingestion/upload", {
    method: "POST",
    body: formData,
  });
}

export async function ingestText(payload: TextIngestionPayload): Promise<IngestionResponse> {
  return fetchJson<IngestionResponse>("/api/ingestion/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function queryText(payload: TextQueryPayload): Promise<RagAnswerResponse> {
  return fetchJson<RagAnswerResponse>("/api/query/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function queryAudio(formData: FormData): Promise<RagAnswerResponse> {
  return fetchJson<RagAnswerResponse>("/api/query/audio", {
    method: "POST",
    body: formData,
  });
}
