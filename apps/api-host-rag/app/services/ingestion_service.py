from app.schemas.common import DocumentStatus, LanguageCode, SourceType
from app.schemas.documents import DocumentMetadata
from app.schemas.ingestion import CuratedSyncResponse, IngestionJobResponse


def parse_topic_tags(topic_tags: str | None) -> list[str]:
    if not topic_tags:
        return []
    return [tag.strip() for tag in topic_tags.split(",") if tag.strip()]


async def upload_document(
    *,
    filename: str | None,
    title: str | None,
    topic_tags: str | None,
    language: LanguageCode,
) -> IngestionJobResponse:
    safe_filename = filename or "document"
    doc_id = f"upload-{safe_filename}"
    document = DocumentMetadata(
        doc_id=doc_id,
        title=title or safe_filename,
        source_type=SourceType.UPLOADED,
        topic_tags=parse_topic_tags(topic_tags),
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


async def sync_curated_corpus() -> CuratedSyncResponse:
    return CuratedSyncResponse(
        status="not_implemented",
        indexed_documents=0,
        skipped_documents=0,
        failed_documents=0,
    )

