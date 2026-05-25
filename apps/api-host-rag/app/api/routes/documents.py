from fastapi import APIRouter, HTTPException

from app.schemas.common import DocumentStatus, LanguageCode, SourceType
from app.schemas.documents import DocumentDetail, DocumentListResponse, DocumentSummary

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _mock_documents() -> list[DocumentSummary]:
    return [
        DocumentSummary(
            doc_id="curated-sleep-basics",
            title="Sleep Hygiene Basics",
            source_type=SourceType.CURATED,
            language=LanguageCode.EN,
            status=DocumentStatus.INDEXED,
            topic_tags=["sleep", "stress"],
            chunk_count=0,
        )
    ]


@router.get("", response_model=DocumentListResponse)
async def list_documents() -> DocumentListResponse:
    return DocumentListResponse(documents=_mock_documents())


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(doc_id: str) -> DocumentDetail:
    for document in _mock_documents():
        if document.doc_id == doc_id:
            return DocumentDetail(**document.model_dump(), chunks=[], metadata={})
    raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

