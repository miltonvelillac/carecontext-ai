export type LanguageCode = "auto" | "en" | "es";
export type SourceType = "curated" | "uploaded";
export type DocumentStatus = "uploaded" | "extracted" | "indexing" | "indexed" | "failed";
export type ApiStatus = "checking" | "online" | "offline";

export type DocumentSummary = {
  doc_id: string;
  title: string;
  source_type: SourceType;
  language: LanguageCode;
  status: DocumentStatus;
  topic_tags: string[];
  chunk_count: number;
  created_at: string | null;
};

export type IngestionResponse = {
  doc_id: string;
  status: DocumentStatus;
  source_type: SourceType;
  message: string;
  document: DocumentSummary | null;
};

export type Citation = {
  doc_id: string;
  title: string;
  chunk_id: string;
  snippet: string;
  section: string | null;
  score: number | null;
  metadata: Record<string, string>;
};

export type RetrievedContextChunk = {
  doc_id: string;
  title: string;
  chunk_id: string;
  snippet: string;
  score: number;
  section: string | null;
  metadata: Record<string, string>;
};

export type SafetyAssessment = {
  risk_level: "low" | "medium" | "high" | "crisis";
  action: "allow" | "caveat" | "redirect";
  disclaimer: string;
  reasons: string[];
  escalation_message: string | null;
};

export type RagAnswerResponse = {
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

export type TextIngestionPayload = {
  text: string;
  title: string | null;
  topic_tags: string[];
  language: LanguageCode;
};

export type TextQueryPayload = {
  query: string;
  language: LanguageCode;
  top_k: number;
  filters: {
    source_types: SourceType[];
    topic_tags: string[];
    language: LanguageCode;
  } | null;
  include_tts: boolean;
};

export type ApiValidationIssue = {
  msg?: string;
};
