from app.schemas.documents import DocumentDetail, DocumentListResponse
from app.services.mock_corpus import list_mock_chunks, list_mock_documents


class DocumentNotFoundError(Exception):
    def __init__(self, doc_id: str) -> None:
        super().__init__(f"Document '{doc_id}' not found")
        self.doc_id = doc_id


async def list_documents() -> DocumentListResponse:
    return DocumentListResponse(documents=list_mock_documents())


async def get_document(doc_id: str) -> DocumentDetail:
    for document in list_mock_documents():
        if document.doc_id == doc_id:
            return DocumentDetail(
                **document.model_dump(),
                chunks=list_mock_chunks(doc_id),
                metadata={"mock": "true"},
            )
    raise DocumentNotFoundError(doc_id)

