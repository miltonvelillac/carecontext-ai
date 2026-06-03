import React, { FormEvent, useEffect, useMemo, useState } from "react";
import ReactDOM from "react-dom/client";
import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  FileText,
  Loader2,
  Mic,
  RefreshCw,
  Search,
  Send,
  Upload,
  Volume2,
} from "lucide-react";
import "./styles.css";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type LanguageCode = "auto" | "en" | "es";
type SourceType = "curated" | "uploaded";
type DocumentStatus = "uploaded" | "extracted" | "indexing" | "indexed" | "failed";

type DocumentSummary = {
  doc_id: string;
  title: string;
  source_type: SourceType;
  language: LanguageCode;
  status: DocumentStatus;
  topic_tags: string[];
  chunk_count: number;
  created_at: string | null;
};

type IngestionResponse = {
  doc_id: string;
  status: DocumentStatus;
  source_type: SourceType;
  message: string;
  document: DocumentSummary | null;
};

type Citation = {
  doc_id: string;
  title: string;
  chunk_id: string;
  snippet: string;
  section: string | null;
  score: number | null;
  metadata: Record<string, string>;
};

type RetrievedContextChunk = {
  doc_id: string;
  title: string;
  chunk_id: string;
  snippet: string;
  score: number;
  section: string | null;
  metadata: Record<string, string>;
};

type SafetyAssessment = {
  risk_level: "low" | "medium" | "high" | "crisis";
  action: "allow" | "caveat" | "redirect";
  disclaimer: string;
  reasons: string[];
  escalation_message: string | null;
};

type RagAnswerResponse = {
  answer: string;
  citations: Citation[];
  safety: SafetyAssessment;
  retrieved_context: RetrievedContextChunk[];
  transcription: {
    text: string;
    language: LanguageCode | null;
    provider: string;
    model: string;
    duration_seconds: number | null;
  } | null;
  tts: {
    audio_id: string | null;
    audio_url: string | null;
    content_type: string;
    provider: string;
    model: string;
    duration_seconds: number | null;
  } | null;
  trace_id: string | null;
};

type ApiStatus = "checking" | "online" | "offline";
type BusyAction = "upload" | "query" | "audio" | "refresh" | null;
type ApiValidationIssue = {
  msg?: string;
};

function splitTags(value: string): string[] {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function formatScore(score: number | null): string {
  if (score === null || Number.isNaN(score)) {
    return "n/a";
  }
  return score.toFixed(2);
}

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

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, init);
  if (!response.ok) {
    throw new Error(await parseApiError(response));
  }
  return response.json() as Promise<T>;
}

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadTags, setUploadTags] = useState("");
  const [uploadLanguage, setUploadLanguage] = useState<LanguageCode>("auto");
  const [query, setQuery] = useState("");
  const [queryLanguage, setQueryLanguage] = useState<LanguageCode>("auto");
  const [sourceType, setSourceType] = useState<"all" | SourceType>("all");
  const [filterTags, setFilterTags] = useState("");
  const [topK, setTopK] = useState(5);
  const [includeTts, setIncludeTts] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [answer, setAnswer] = useState<RagAnswerResponse | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<BusyAction>(null);

  const indexedCount = useMemo(
    () => documents.filter((document) => document.status === "indexed").length,
    [documents],
  );

  async function checkHealth() {
    try {
      await fetchJson<{ status: string }>("/health");
      setApiStatus("online");
    } catch {
      setApiStatus("offline");
    }
  }

  async function loadDocuments() {
    setBusy((current) => current ?? "refresh");
    try {
      const payload = await fetchJson<{ documents: DocumentSummary[] }>("/api/documents");
      setDocuments(payload.documents);
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load documents.");
    } finally {
      setBusy((current) => (current === "refresh" ? null : current));
    }
  }

  useEffect(() => {
    void checkHealth();
    void loadDocuments();
  }, []);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      setError("Choose a PDF before uploading.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    if (uploadTitle.trim()) {
      formData.append("title", uploadTitle.trim());
    }
    if (uploadTags.trim()) {
      formData.append("topic_tags", uploadTags.trim());
    }
    formData.append("language", uploadLanguage);

    setBusy("upload");
    setError(null);
    setNotice(null);
    try {
      const payload = await fetchJson<IngestionResponse>("/api/ingestion/upload", {
        method: "POST",
        body: formData,
      });
      setNotice(payload.message);
      setSelectedFile(null);
      setUploadTitle("");
      setUploadTags("");
      await loadDocuments();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
    } finally {
      setBusy(null);
    }
  }

  async function submitTextQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) {
      setError("Write a question before submitting.");
      return;
    }

    const sourceTypes = sourceType === "all" ? [] : [sourceType];
    const topicTags = splitTags(filterTags);
    const filters =
      sourceTypes.length || topicTags.length || queryLanguage !== "auto"
        ? {
            source_types: sourceTypes,
            topic_tags: topicTags,
            language: queryLanguage,
          }
        : null;

    setBusy("query");
    setError(null);
    setNotice(null);
    try {
      const payload = await fetchJson<RagAnswerResponse>("/api/query/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          language: queryLanguage,
          top_k: topK,
          filters,
          include_tts: includeTts,
        }),
      });
      setAnswer(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Query failed.");
    } finally {
      setBusy(null);
    }
  }

  async function submitAudioQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!audioFile) {
      setError("Choose an audio file before submitting.");
      return;
    }

    const formData = new FormData();
    formData.append("file", audioFile);
    formData.append("language", queryLanguage);
    formData.append("top_k", String(topK));
    formData.append("include_tts", String(includeTts));

    setBusy("audio");
    setError(null);
    setNotice(null);
    try {
      const payload = await fetchJson<RagAnswerResponse>("/api/query/audio", {
        method: "POST",
        body: formData,
      });
      setAnswer(payload);
      setAudioFile(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Audio query failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="app-header">
          <div>
            <p className="eyebrow">CareContext AI</p>
            <h1>Health and psychology RAG assistant</h1>
          </div>
          <div className={`api-pill ${apiStatus}`}>
            <span className="status-dot" />
            <span>{apiStatus === "checking" ? "Checking API" : `API ${apiStatus}`}</span>
          </div>
        </header>

        {(notice || error) && (
          <div className={`banner ${error ? "error" : "success"}`}>
            {error ? <AlertTriangle aria-hidden="true" /> : <CheckCircle2 aria-hidden="true" />}
            <span>{error ?? notice}</span>
          </div>
        )}

        <div className="layout">
          <section className="panel upload-panel">
            <div className="panel-heading">
              <Upload aria-hidden="true" />
              <div>
                <p className="section-label">Upload</p>
                <h2>Index a PDF</h2>
              </div>
            </div>

            <form className="form-stack" onSubmit={handleUpload}>
              <label className="field">
                <span>PDF file</span>
                <input
                  accept="application/pdf,.pdf"
                  type="file"
                  onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                />
              </label>

              <label className="field">
                <span>Title</span>
                <input
                  placeholder="Sleep Hygiene Basics"
                  type="text"
                  value={uploadTitle}
                  onChange={(event) => setUploadTitle(event.target.value)}
                />
              </label>

              <div className="two-col">
                <label className="field">
                  <span>Language</span>
                  <select
                    value={uploadLanguage}
                    onChange={(event) => setUploadLanguage(event.target.value as LanguageCode)}
                  >
                    <option value="auto">Auto</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                  </select>
                </label>

                <label className="field">
                  <span>Tags</span>
                  <input
                    placeholder="sleep, stress"
                    type="text"
                    value={uploadTags}
                    onChange={(event) => setUploadTags(event.target.value)}
                  />
                </label>
              </div>

              <button className="primary-button" disabled={busy === "upload"} type="submit">
                {busy === "upload" ? <Loader2 aria-hidden="true" /> : <Upload aria-hidden="true" />}
                <span>{busy === "upload" ? "Uploading" : "Upload and index"}</span>
              </button>
            </form>
          </section>

          <section className="panel corpus-panel">
            <div className="panel-heading row-heading">
              <div className="title-row">
                <BookOpen aria-hidden="true" />
                <div>
                  <p className="section-label">Corpus</p>
                  <h2>{indexedCount} indexed documents</h2>
                </div>
              </div>
              <button
                aria-label="Refresh documents"
                className="icon-button"
                disabled={busy === "refresh"}
                type="button"
                onClick={() => void loadDocuments()}
              >
                <RefreshCw aria-hidden="true" />
              </button>
            </div>

            <div className="document-list">
              {documents.length === 0 ? (
                <div className="empty-state">
                  <FileText aria-hidden="true" />
                  <span>No documents indexed yet.</span>
                </div>
              ) : (
                documents.map((document) => (
                  <article className="document-row" key={document.doc_id}>
                    <div>
                      <h3>{document.title}</h3>
                      <p>{document.doc_id}</p>
                    </div>
                    <div className="document-meta">
                      <span className={`status-badge ${document.status}`}>{document.status}</span>
                      <span>{document.source_type}</span>
                      <span>{document.language}</span>
                      <span>{document.chunk_count} chunks</span>
                    </div>
                    {document.topic_tags.length > 0 && (
                      <div className="tag-row">
                        {document.topic_tags.map((tag) => (
                          <span key={`${document.doc_id}-${tag}`}>{tag}</span>
                        ))}
                      </div>
                    )}
                  </article>
                ))
              )}
            </div>
          </section>

          <section className="panel ask-panel">
            <div className="panel-heading">
              <Search aria-hidden="true" />
              <div>
                <p className="section-label">Ask</p>
                <h2>Query the corpus</h2>
              </div>
            </div>

            <form className="form-stack" onSubmit={submitTextQuery}>
              <label className="field">
                <span>Question</span>
                <textarea
                  placeholder="How can sleep routines help with stress?"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </label>

              <div className="three-col">
                <label className="field">
                  <span>Language</span>
                  <select
                    value={queryLanguage}
                    onChange={(event) => setQueryLanguage(event.target.value as LanguageCode)}
                  >
                    <option value="auto">Auto</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                  </select>
                </label>

                <label className="field">
                  <span>Source</span>
                  <select
                    value={sourceType}
                    onChange={(event) => setSourceType(event.target.value as "all" | SourceType)}
                  >
                    <option value="all">All</option>
                    <option value="curated">Curated</option>
                    <option value="uploaded">Uploaded</option>
                  </select>
                </label>

                <label className="field">
                  <span>Top K</span>
                  <input
                    max={20}
                    min={1}
                    type="number"
                    value={topK}
                    onChange={(event) => setTopK(Number(event.target.value))}
                  />
                </label>
              </div>

              <label className="field">
                <span>Filter tags</span>
                <input
                  placeholder="sleep, anxiety"
                  type="text"
                  value={filterTags}
                  onChange={(event) => setFilterTags(event.target.value)}
                />
              </label>

              <label className="check-field">
                <input
                  checked={includeTts}
                  type="checkbox"
                  onChange={(event) => setIncludeTts(event.target.checked)}
                />
                <span>Request TTS metadata</span>
              </label>

              <button className="primary-button" disabled={busy === "query"} type="submit">
                {busy === "query" ? <Loader2 aria-hidden="true" /> : <Send aria-hidden="true" />}
                <span>{busy === "query" ? "Asking" : "Ask question"}</span>
              </button>
            </form>

            <form className="audio-strip" onSubmit={submitAudioQuery}>
              <label className="field compact-field">
                <span>Audio question</span>
                <input
                  accept="audio/*"
                  type="file"
                  onChange={(event) => setAudioFile(event.target.files?.[0] ?? null)}
                />
              </label>
              <button className="secondary-button" disabled={busy === "audio"} type="submit">
                {busy === "audio" ? <Loader2 aria-hidden="true" /> : <Mic aria-hidden="true" />}
                <span>{busy === "audio" ? "Sending" : "Send audio"}</span>
              </button>
            </form>
          </section>

          <section className="panel answer-panel">
            <div className="panel-heading">
              <Volume2 aria-hidden="true" />
              <div>
                <p className="section-label">Answer</p>
                <h2>Grounded response</h2>
              </div>
            </div>

            {!answer ? (
              <div className="empty-state answer-empty">
                <Search aria-hidden="true" />
                <span>Answers and citations appear after a query.</span>
              </div>
            ) : (
              <div className="answer-content">
                {answer.transcription && (
                  <div className="transcription-box">
                    <strong>Transcription</strong>
                    <p>{answer.transcription.text}</p>
                  </div>
                )}

                <div className={`safety-card ${answer.safety.risk_level}`}>
                  <strong>{answer.safety.risk_level} risk</strong>
                  <span>{answer.safety.disclaimer}</span>
                  {answer.safety.escalation_message && (
                    <span>{answer.safety.escalation_message}</span>
                  )}
                </div>

                <p className="answer-text">{answer.answer}</p>

                {answer.tts && (
                  <div className="tts-row">
                    <Volume2 aria-hidden="true" />
                    <span>
                      TTS: {answer.tts.provider} / {answer.tts.model}
                    </span>
                  </div>
                )}

                <div className="citation-list">
                  <h3>Citations</h3>
                  {answer.citations.length === 0 ? (
                    <p className="muted-text">No citations returned.</p>
                  ) : (
                    answer.citations.map((citation) => (
                      <article className="citation" key={citation.chunk_id}>
                        <div className="citation-header">
                          <strong>{citation.title}</strong>
                          <span>{formatScore(citation.score)}</span>
                        </div>
                        <p>{citation.snippet}</p>
                        <span className="chunk-id">{citation.chunk_id}</span>
                      </article>
                    ))
                  )}
                </div>

                {answer.trace_id && <p className="trace-id">Trace: {answer.trace_id}</p>}
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
