from typing import Protocol

from pydantic import BaseModel, Field

from app.schemas.common import LanguageCode


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


class DocumentToolsPort(Protocol):
    async def extract_text_from_pdf(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ExtractedDocument:
        ...

    async def clean_extracted_text(self, text: str) -> CleanedDocumentText:
        ...

    async def get_document_metadata(
        self,
        text: str,
        filename: str,
        user_title: str | None = None,
    ) -> DocumentToolMetadata:
        ...
