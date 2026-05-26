from app.adapters.mock.corpus import list_mock_chunks, list_mock_documents
from app.ports.document_repository import DocumentRepositoryPort
from app.schemas.documents import DocumentDetail, DocumentSummary


class MockDocumentRepository(DocumentRepositoryPort):
    async def list_documents(self) -> list[DocumentSummary]:
        return list_mock_documents()

    async def get_document(self, doc_id: str) -> DocumentDetail | None:
        for document in list_mock_documents():
            if document.doc_id == doc_id:
                return DocumentDetail(
                    **document.model_dump(),
                    chunks=list_mock_chunks(doc_id),
                    metadata={"mock": "true"},
                )
        return None
