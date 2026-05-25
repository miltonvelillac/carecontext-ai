from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.common import DocumentStatus, LanguageCode, SourceType
from app.schemas.documents import DocumentMetadata
from app.schemas.ingestion import CuratedSyncResponse, IngestionJobResponse

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])


def _parse_topic_tags(topic_tags: str | None) -> list[str]:
    if not topic_tags:
        return []
    return [tag.strip() for tag in topic_tags.split(",") if tag.strip()]


@router.post("/upload", response_model=IngestionJobResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    topic_tags: str | None = Form(default=None),
    language: LanguageCode = Form(default=LanguageCode.AUTO),
) -> IngestionJobResponse:
    doc_id = f"upload-{file.filename or 'document'}"
    document = DocumentMetadata(
        doc_id=doc_id,
        title=title or file.filename or "Uploaded document",
        source_type=SourceType.UPLOADED,
        topic_tags=_parse_topic_tags(topic_tags),
        language=language,
        status=DocumentStatus.UPLOADED,
    )
    return IngestionJobResponse(
        doc_id=doc_id,
        status=DocumentStatus.UPLOADED,
        source_type=SourceType.UPLOADED,
        message="Upload accepted. Extraction and indexing are not implemented yet.",
        document=document,
    )


@router.post("/curated/sync", response_model=CuratedSyncResponse)
async def sync_curated_corpus() -> CuratedSyncResponse:
    return CuratedSyncResponse(
        status="not_implemented",
        indexed_documents=0,
        skipped_documents=0,
        failed_documents=0,
    )

