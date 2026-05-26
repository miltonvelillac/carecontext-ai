from typing import Protocol

from app.schemas.documents import DocumentDetail, DocumentSummary


class DocumentRepositoryPort(Protocol):
    """Repository port for document read models.

    Repository Pattern: application code asks this abstraction for documents,
    while storage details stay behind concrete repository adapters.
    """

    async def list_documents(self) -> list[DocumentSummary]:
        ...

    async def get_document(self, doc_id: str) -> DocumentDetail | None:
        ...
