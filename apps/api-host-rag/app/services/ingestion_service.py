"""Ingestion use cases.

Service Layer: routes translate HTTP into Python values, then this module
coordinates ports such as document processing and retrieval indexing.
"""

from app.ports.document_tools import DocumentToolsPort
from app.ports.retrieval_tools import RetrievalToolsPort
from app.schemas.common import DocumentStatus, LanguageCode, SourceType
from app.schemas.documents import DocumentChunk, DocumentMetadata
from app.schemas.ingestion import CuratedSyncResponse, IngestionJobResponse


def _parse_topic_tags(topic_tags: str | None) -> list[str]:
    if not topic_tags:
        return []
    return [tag.strip() for tag in topic_tags.split(",") if tag.strip()]


async def upload_document(
    *,
    content: bytes,
    filename: str | None,
    content_type: str | None,
    title: str | None,
    topic_tags: str | None,
    language: LanguageCode,
    document_tools: DocumentToolsPort,
    retrieval_tools: RetrievalToolsPort,
) -> IngestionJobResponse:
    safe_filename = filename or "document"
    doc_id = f"upload-{safe_filename}"
    extracted = await document_tools.extract_text_from_pdf(content, safe_filename, content_type)
    cleaned = await document_tools.clean_extracted_text(extracted.text)
    tool_metadata = await document_tools.get_document_metadata(cleaned.text, safe_filename, title)

    resolved_title = title or tool_metadata.title or safe_filename
    resolved_topic_tags = _parse_topic_tags(topic_tags) or tool_metadata.topic_tags
    resolved_language = language if language != LanguageCode.AUTO else tool_metadata.language

    document = DocumentMetadata(
        doc_id=doc_id,
        title=resolved_title,
        source_type=SourceType.UPLOADED,
        topic_tags=resolved_topic_tags,
        language=resolved_language,
        status=DocumentStatus.UPLOADED,
        quality_score=tool_metadata.quality_score,
    )
    chunk = DocumentChunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}-chunk-001",
        title=resolved_title,
        text=cleaned.text,
        source_type=SourceType.UPLOADED,
        topic_tags=resolved_topic_tags,
        language=resolved_language,
        section=tool_metadata.section_titles[0] if tool_metadata.section_titles else None,
        quality_score=tool_metadata.quality_score,
        metadata={**extracted.metadata, **tool_metadata.metadata},
    )
    upsert_result = await retrieval_tools.upsert_chunks([chunk])
    return IngestionJobResponse(
        doc_id=doc_id,
        status=DocumentStatus.UPLOADED,
        source_type=SourceType.UPLOADED,
        message=(
            "Upload accepted and processed with mock document/retrieval adapters. "
            f"Inserted chunks: {upsert_result.inserted_count}."
        ),
        document=document,
    )


async def sync_curated_corpus() -> CuratedSyncResponse:
    return CuratedSyncResponse(
        status="not_implemented",
        indexed_documents=0,
        skipped_documents=0,
        failed_documents=0,
    )
