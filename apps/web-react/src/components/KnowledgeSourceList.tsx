import { FileText, RefreshCw } from "lucide-react";
import type { DocumentSummary } from "../types";
import { Button } from "./ui/Button";

type KnowledgeSourceListProps = {
  documents: DocumentSummary[];
  isRefreshing: boolean;
  onRefresh: () => void;
};

export function KnowledgeSourceList({
  documents,
  isRefreshing,
  onRefresh,
}: KnowledgeSourceListProps) {
  const indexedCount = documents.filter((document) => document.status === "indexed").length;

  return (
    <div className="source-list-block">
      <div className="section-toolbar">
        <div>
          <p className="section-label">Loaded context</p>
          <h3>{indexedCount} indexed sources</h3>
        </div>
        <Button
          aria-label="Refresh sources"
          icon={<RefreshCw aria-hidden="true" />}
          isLoading={isRefreshing}
          type="button"
          variant="ghost"
          onClick={onRefresh}
        >
          Refresh
        </Button>
      </div>

      <div className="source-list">
        {documents.length === 0 ? (
          <div className="empty-state compact">
            <FileText aria-hidden="true" />
            <span>No sources indexed yet.</span>
          </div>
        ) : (
          documents.map((document) => (
            <article className="source-row" key={document.doc_id}>
              <div>
                <strong>{document.title}</strong>
                <p>{document.doc_id}</p>
              </div>
              <div className="source-meta">
                <span className={`status-badge ${document.status}`}>{document.status}</span>
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
    </div>
  );
}
