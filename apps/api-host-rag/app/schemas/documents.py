from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import DocumentStatus, LanguageCode, SourceType


class DocumentMetadata(BaseModel):
    doc_id: str
    title: str
    source_type: SourceType
    topic_tags: list[str] = Field(default_factory=list)
    language: LanguageCode = LanguageCode.AUTO
    status: DocumentStatus = DocumentStatus.UPLOADED
    created_at: datetime | None = None
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)


class DocumentChunk(BaseModel):
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


class DocumentSummary(BaseModel):
    doc_id: str
    title: str
    source_type: SourceType
    language: LanguageCode
    status: DocumentStatus
    topic_tags: list[str] = Field(default_factory=list)
    chunk_count: int = Field(default=0, ge=0)
    created_at: datetime | None = None


class DocumentDetail(DocumentSummary):
    chunks: list[DocumentChunk] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary] = Field(default_factory=list)

