from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from carecontext_contracts.common import LanguageCode, SourceType


class RetrievalMcpToolName(StrEnum):
    CHUNK_DOCUMENT = "chunk_document"
    UPSERT_CHUNKS = "upsert_chunks"
    HYBRID_SEARCH = "hybrid_search"
    RERANK_RESULTS = "rerank_results"


class RetrievalMcpArgumentName(StrEnum):
    REQUEST = "request"
    CHUNKS = "chunks"
    QUERY = "query"
    TOP_K = "top_k"
    FILTERS = "filters"
    RESULTS = "results"


class RetrievalEmbeddingsProvider(StrEnum):
    DETERMINISTIC = "deterministic"
    OPENAI = "openai"


class ChunkDocumentRequest(BaseModel):
    doc_id: str
    title: str
    text: str
    source_type: SourceType
    topic_tags: list[str] = Field(default_factory=list)
    language: LanguageCode = LanguageCode.AUTO
    section: str | None = None
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, str] = Field(default_factory=dict)
    chunk_size: int = Field(default=1000, ge=100, le=8000)
    chunk_overlap: int = Field(default=150, ge=0, le=2000)


class RetrievalDocumentChunk(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    text: str
    source_type: SourceType
    topic_tags: list[str] = Field(default_factory=list)
    language: LanguageCode = LanguageCode.AUTO
    section: str | None = None
    created_at: datetime | None = None
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, str] = Field(default_factory=dict)


class ChunkDocumentResult(BaseModel):
    chunks: list[RetrievalDocumentChunk] = Field(default_factory=list)


class RetrievalFilter(BaseModel):
    source_types: list[SourceType] = Field(default_factory=list)
    topic_tags: list[str] = Field(default_factory=list)
    language: LanguageCode = LanguageCode.AUTO
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)


class UpsertChunksResult(BaseModel):
    inserted_count: int = Field(ge=0)
    updated_count: int = Field(default=0, ge=0)
    skipped_count: int = Field(default=0, ge=0)
    collection_name: str | None = None


class RetrievedChunk(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    snippet: str
    score: float
    section: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class HybridSearchResult(BaseModel):
    results: list[RetrievedChunk] = Field(default_factory=list)


class RerankedChunk(BaseModel):
    chunk: RetrievedChunk
    rerank_score: float
    reason: str | None = None


class RerankResultsResult(BaseModel):
    results: list[RerankedChunk] = Field(default_factory=list)
