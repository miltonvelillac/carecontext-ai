from typing import Protocol

from app.schemas.documents import DocumentChunk, DocumentDetail, DocumentMetadata, DocumentSummary


class DocumentRepositoryPort(Protocol):
    """Repository port for document read models.

    Repository Pattern: application code asks this abstraction for documents,
    while storage details stay behind concrete repository adapters.
    """

    async def list_documents(self) -> list[DocumentSummary]:
        ...

    async def get_document(self, doc_id: str) -> DocumentDetail | None:
        ...

    async def save_document(
        self,
        document: DocumentMetadata,
        chunks: list[DocumentChunk],
        metadata: dict[str, str] | None = None,
    ) -> DocumentDetail:
        ...
