import { FormEvent, useState } from "react";
import { FileUp, StickyNote, Upload } from "lucide-react";
import type { DocumentSummary, LanguageCode, TextIngestionPayload } from "../types";
import { splitTags } from "../utils/format";
import { Button } from "./ui/Button";
import { KnowledgeSourceList } from "./KnowledgeSourceList";

type ContentIngestionSectionProps = {
  documents: DocumentSummary[];
  isRefreshing: boolean;
  isSubmitting: boolean;
  onRefreshDocuments: () => void;
  onSubmitDocument: (formData: FormData) => Promise<void>;
  onSubmitText: (payload: TextIngestionPayload) => Promise<void>;
};

export function ContentIngestionSection({
  documents,
  isRefreshing,
  isSubmitting,
  onRefreshDocuments,
  onSubmitDocument,
  onSubmitText,
}: ContentIngestionSectionProps) {
  const [file, setFile] = useState<File | null>(null);
  const [documentTitle, setDocumentTitle] = useState("");
  const [documentTags, setDocumentTags] = useState("");
  const [documentLanguage, setDocumentLanguage] = useState<LanguageCode>("auto");
  const [textTitle, setTextTitle] = useState("");
  const [textTags, setTextTags] = useState("");
  const [textLanguage, setTextLanguage] = useState<LanguageCode>("auto");
  const [text, setText] = useState("");

  async function handleDocumentSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    if (documentTitle.trim()) {
      formData.append("title", documentTitle.trim());
    }
    if (documentTags.trim()) {
      formData.append("topic_tags", documentTags.trim());
    }
    formData.append("language", documentLanguage);

    await onSubmitDocument(formData);
    setFile(null);
    setDocumentTitle("");
    setDocumentTags("");
  }

  async function handleTextSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!text.trim()) {
      return;
    }

    await onSubmitText({
      text: text.trim(),
      title: textTitle.trim() || null,
      topic_tags: splitTags(textTags),
      language: textLanguage,
    });
    setText("");
    setTextTitle("");
    setTextTags("");
  }

  return (
    <section className="workspace-card load-card">
      <div className="card-intro">
        <div className="icon-plate">
          <Upload aria-hidden="true" />
        </div>
        <div>
          <p className="section-label">Load context</p>
          <h2>Documents or pasted notes</h2>
        </div>
      </div>

      <div className="ingestion-grid">
        <form className="mini-panel" onSubmit={handleDocumentSubmit}>
          <div className="mini-panel-title">
            <FileUp aria-hidden="true" />
            <strong>PDF document</strong>
          </div>
          <label className="field">
            <span>File</span>
            <input
              accept="application/pdf,.pdf"
              type="file"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <label className="field">
            <span>Title</span>
            <input
              placeholder="Sleep protocol"
              type="text"
              value={documentTitle}
              onChange={(event) => setDocumentTitle(event.target.value)}
            />
          </label>
          <div className="split-fields">
            <label className="field">
              <span>Language</span>
              <select
                value={documentLanguage}
                onChange={(event) => setDocumentLanguage(event.target.value as LanguageCode)}
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
                value={documentTags}
                onChange={(event) => setDocumentTags(event.target.value)}
              />
            </label>
          </div>
          <Button
            disabled={!file || isSubmitting}
            icon={<Upload aria-hidden="true" />}
            isLoading={isSubmitting}
            type="submit"
          >
            Index PDF
          </Button>
        </form>

        <form className="mini-panel text-panel" onSubmit={handleTextSubmit}>
          <div className="mini-panel-title">
            <StickyNote aria-hidden="true" />
            <strong>Pasted text</strong>
          </div>
          <label className="field">
            <span>Title</span>
            <input
              placeholder="Session notes"
              type="text"
              value={textTitle}
              onChange={(event) => setTextTitle(event.target.value)}
            />
          </label>
          <label className="field">
            <span>Text</span>
            <textarea
              placeholder="Paste source text here..."
              value={text}
              onChange={(event) => setText(event.target.value)}
            />
          </label>
          <div className="split-fields">
            <label className="field">
              <span>Language</span>
              <select
                value={textLanguage}
                onChange={(event) => setTextLanguage(event.target.value as LanguageCode)}
              >
                <option value="auto">Auto</option>
                <option value="en">English</option>
                <option value="es">Spanish</option>
              </select>
            </label>
            <label className="field">
              <span>Tags</span>
              <input
                placeholder="anxiety, coping"
                type="text"
                value={textTags}
                onChange={(event) => setTextTags(event.target.value)}
              />
            </label>
          </div>
          <Button
            disabled={!text.trim() || isSubmitting}
            icon={<StickyNote aria-hidden="true" />}
            isLoading={isSubmitting}
            type="submit"
          >
            Index text
          </Button>
        </form>
      </div>

      <KnowledgeSourceList
        documents={documents}
        isRefreshing={isRefreshing}
        onRefresh={onRefreshDocuments}
      />
    </section>
  );
}
