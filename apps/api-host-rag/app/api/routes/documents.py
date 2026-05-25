from fastapi import APIRouter, HTTPException

from app.schemas.documents import DocumentDetail, DocumentListResponse
from app.services.document_service import DocumentNotFoundError, get_document, list_documents

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents_endpoint() -> DocumentListResponse:
    return await list_documents()


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document_endpoint(doc_id: str) -> DocumentDetail:
    try:
        return await get_document(doc_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
