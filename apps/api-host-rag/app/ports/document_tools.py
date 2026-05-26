from typing import Protocol

from carecontext_contracts.document_mcp import (
    CleanedDocumentText,
    DocumentToolMetadata,
    ExtractedDocument,
)


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
