from carecontext_contracts.common import MetadataKey, MetadataValue

from app.adapters.mock.corpus import list_mock_chunks, list_mock_documents
from app.ports.document_repository import DocumentRepositoryPort
from app.schemas.documents import DocumentChunk, DocumentDetail, DocumentMetadata, DocumentSummary


class MockDocumentRepository(DocumentRepositoryPort):
    async def list_documents(self) -> list[DocumentSummary]:
        return list_mock_documents()

    async def get_document(self, doc_id: str) -> DocumentDetail | None:
        for document in list_mock_documents():
            if document.doc_id == doc_id:
                return DocumentDetail(
                    **document.model_dump(),
                    chunks=list_mock_chunks(doc_id),
                    metadata={MetadataKey.MOCK: MetadataValue.TRUE},
                )
        return None

    async def save_document(
        self,
        document: DocumentMetadata,
        chunks: list[DocumentChunk],
        metadata: dict[str, str] | None = None,
    ) -> DocumentDetail:
        return DocumentDetail(
            doc_id=document.doc_id,
            title=document.title,
            source_type=document.source_type,
            language=document.language,
            status=document.status,
            topic_tags=document.topic_tags,
            chunk_count=len(chunks),
            created_at=document.created_at,
            chunks=chunks,
            metadata=metadata or {},
        )
