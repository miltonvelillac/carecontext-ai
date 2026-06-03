import { useEffect, useState } from "react";
import {
  checkHealth,
  ingestText,
  listDocuments,
  queryAudio,
  queryText,
  uploadDocument,
} from "./api/client";
import { AppHeader } from "./components/AppHeader";
import { ContentIngestionSection } from "./components/ContentIngestionSection";
import { NoticeBanner } from "./components/NoticeBanner";
import { QuestionSection } from "./components/QuestionSection";
import type {
  ApiStatus,
  DocumentSummary,
  RagAnswerResponse,
  TextIngestionPayload,
  TextQueryPayload,
} from "./types";

type BusyAction = "upload" | "text" | "query" | "audio" | "refresh" | null;

export function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [answer, setAnswer] = useState<RagAnswerResponse | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<BusyAction>(null);

  async function refreshDocuments() {
    setBusy((current) => current ?? "refresh");
    try {
      setDocuments(await listDocuments());
      setError(null);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load sources.");
    } finally {
      setBusy((current) => (current === "refresh" ? null : current));
    }
  }

  useEffect(() => {
    async function bootstrap() {
      try {
        await checkHealth();
        setApiStatus("online");
      } catch {
        setApiStatus("offline");
      }
      await refreshDocuments();
    }

    void bootstrap();
  }, []);

  async function handleDocumentSubmit(formData: FormData) {
    setBusy("upload");
    setError(null);
    setNotice(null);
    try {
      const response = await uploadDocument(formData);
      setNotice(response.message);
      await refreshDocuments();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleTextSubmit(payload: TextIngestionPayload) {
    setBusy("text");
    setError(null);
    setNotice(null);
    try {
      const response = await ingestText(payload);
      setNotice(response.message);
      await refreshDocuments();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Text ingestion failed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleQuestionSubmit(payload: TextQueryPayload) {
    setBusy("query");
    setError(null);
    setNotice(null);
    try {
      setAnswer(await queryText(payload));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Query failed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleAudioSubmit(formData: FormData) {
    setBusy("audio");
    setError(null);
    setNotice(null);
    try {
      setAnswer(await queryAudio(formData));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Audio query failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <AppHeader apiStatus={apiStatus} />
        <NoticeBanner error={error} notice={notice} />
        <div className="workspace-grid">
          <ContentIngestionSection
            documents={documents}
            isRefreshing={busy === "refresh"}
            isSubmitting={busy === "upload" || busy === "text"}
            onRefreshDocuments={() => void refreshDocuments()}
            onSubmitDocument={handleDocumentSubmit}
            onSubmitText={handleTextSubmit}
          />
          <QuestionSection
            answer={answer}
            isSubmittingAudio={busy === "audio"}
            isSubmittingText={busy === "query"}
            onSubmitAudio={handleAudioSubmit}
            onSubmitText={handleQuestionSubmit}
          />
        </div>
      </section>
    </main>
  );
}
