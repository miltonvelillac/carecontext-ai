from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_document_repository
from app.ports.document_repository import DocumentRepositoryPort
from app.schemas.documents import DocumentDetail, DocumentListResponse
from app.services.document_service import DocumentNotFoundError, get_document, list_documents

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
async def list_documents_endpoint(
    repository: DocumentRepositoryPort = Depends(get_document_repository),
) -> DocumentListResponse:
    return await list_documents(repository)


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document_endpoint(
    doc_id: str,
    repository: DocumentRepositoryPort = Depends(get_document_repository),
) -> DocumentDetail:
    try:
        return await get_document(doc_id, repository)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
