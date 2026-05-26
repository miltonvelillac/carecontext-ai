from datetime import datetime
from enum import StrEnum

from carecontext_contracts.common import LanguageCode
from pydantic import BaseModel, Field


class SourceType(StrEnum):
    CURATED = "curated"
    UPLOADED = "uploaded"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class TimestampedModel(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)
