from fastapi import APIRouter, File, Form, UploadFile

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
) -> IngestionJobResponse:
    return await upload_document(
        filename=file.filename,
        title=title,
        topic_tags=topic_tags,
        language=language,
    )


@router.post("/curated/sync", response_model=CuratedSyncResponse)
async def sync_curated_corpus_endpoint() -> CuratedSyncResponse:
    return await sync_curated_corpus()
