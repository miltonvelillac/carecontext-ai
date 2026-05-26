from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_document_tools, get_retrieval_tools
from app.ports.document_tools import DocumentToolsPort
from app.ports.retrieval_tools import RetrievalToolsPort
from app.schemas.common import LanguageCode
from app.schemas.ingestion import CuratedSyncResponse, IngestionJobResponse
from app.services.ingestion_service import sync_curated_corpus, upload_document

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])


@router.post("/upload", response_model=IngestionJobResponse)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    topic_tags: str | None = Form(default=None),
    language: LanguageCode = Form(default=LanguageCode.AUTO),
    document_tools: DocumentToolsPort = Depends(get_document_tools),
    retrieval_tools: RetrievalToolsPort = Depends(get_retrieval_tools),
) -> IngestionJobResponse:
    content = await file.read()
    return await upload_document(
        content=content,
        filename=file.filename,
        content_type=file.content_type,
        title=title,
        topic_tags=topic_tags,
        language=language,
        document_tools=document_tools,
        retrieval_tools=retrieval_tools,
    )


@router.post("/curated/sync", response_model=CuratedSyncResponse)
async def sync_curated_corpus_endpoint() -> CuratedSyncResponse:
    return await sync_curated_corpus()
