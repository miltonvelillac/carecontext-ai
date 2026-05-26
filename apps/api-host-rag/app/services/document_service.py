from app.ports.document_repository import DocumentRepositoryPort
from app.schemas.documents import DocumentDetail, DocumentListResponse


class DocumentNotFoundError(Exception):
    def __init__(self, doc_id: str) -> None:
        super().__init__(f"Document '{doc_id}' not found")
        self.doc_id = doc_id


async def list_documents(repository: DocumentRepositoryPort) -> DocumentListResponse:
    return DocumentListResponse(documents=await repository.list_documents())


async def get_document(doc_id: str, repository: DocumentRepositoryPort) -> DocumentDetail:
    document = await repository.get_document(doc_id)
    if document is not None:
        return document
    raise DocumentNotFoundError(doc_id)
