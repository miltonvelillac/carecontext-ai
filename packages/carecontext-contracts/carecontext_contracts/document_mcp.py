from enum import StrEnum

from pydantic import BaseModel, Field

from carecontext_contracts.common import LanguageCode


class DocumentMcpToolName(StrEnum):
    EXTRACT_TEXT_FROM_PDF = "extract_text_from_pdf"
    CLEAN_EXTRACTED_TEXT = "clean_extracted_text"
    GET_DOCUMENT_METADATA = "get_document_metadata"


class DocumentMcpArgumentName(StrEnum):
    CONTENT_BASE64 = "content_base64"
    CONTENT_TYPE = "content_type"
    FILENAME = "filename"
    TEXT = "text"
    USER_TITLE = "user_title"


class ExtractedDocument(BaseModel):
    text: str
    filename: str
    content_type: str | None = None
    page_count: int | None = Field(default=None, ge=0)
    metadata: dict[str, str] = Field(default_factory=dict)


class CleanedDocumentText(BaseModel):
    text: str
    removed_sections: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocumentToolMetadata(BaseModel):
    title: str | None = None
    language: LanguageCode = LanguageCode.AUTO
    topic_tags: list[str] = Field(default_factory=list)
    section_titles: list[str] = Field(default_factory=list)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, str] = Field(default_factory=dict)
