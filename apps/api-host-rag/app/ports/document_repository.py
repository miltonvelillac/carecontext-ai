from typing import Protocol

from app.schemas.documents import DocumentDetail, DocumentSummary


class DocumentRepositoryPort(Protocol):
    async def list_documents(self) -> list[DocumentSummary]:
        ...

    async def get_document(self, doc_id: str) -> DocumentDetail | None:
        ...

