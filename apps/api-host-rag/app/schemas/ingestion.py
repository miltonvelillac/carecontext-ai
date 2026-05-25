from pydantic import BaseModel, Field

from app.schemas.common import DocumentStatus, LanguageCode, SourceType
from app.schemas.documents import DocumentMetadata


class UploadDocumentRequestMetadata(BaseModel):
    title: str | None = None
    topic_tags: list[str] = Field(default_factory=list)
    language: LanguageCode = LanguageCode.AUTO


class IngestionJobResponse(BaseModel):
    doc_id: str
    status: DocumentStatus
    source_type: SourceType
    message: str
    document: DocumentMetadata | None = None


class CuratedSyncResponse(BaseModel):
    status: str
    indexed_documents: int = Field(default=0, ge=0)
    skipped_documents: int = Field(default=0, ge=0)
    failed_documents: int = Field(default=0, ge=0)

