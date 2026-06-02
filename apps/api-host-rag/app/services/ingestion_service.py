"""Ingestion use cases.

Service Layer: routes translate HTTP into Python values, then this module
coordinates ports such as document processing and retrieval indexing.
"""

from datetime import UTC, datetime

from app.ports.document_repository import DocumentRepositoryPort
from app.ports.document_tools import DocumentToolsPort
from app.ports.retrieval_tools import RetrievalToolsPort
from app.schemas.common import DocumentStatus, LanguageCode, SourceType
from app.schemas.documents import DocumentChunk, DocumentMetadata
from app.schemas.ingestion import CuratedSyncResponse, IngestionJobResponse


def _parse_topic_tags(topic_tags: str | None) -> list[str]:
    if not topic_tags:
        return []
    return [tag.strip() for tag in topic_tags.split(",") if tag.strip()]


def _metadata_with_error(
    metadata: dict[str, str] | None,
    *,
    error_code: str,
    error_message: str,
) -> dict[str, str]:
    return {
        **(metadata or {}),
        "ingestion_error_code": error_code,
        "ingestion_error_message": error_message,
    }


async def _save_failed_document(
    *,
    doc_id: str,
    title: str,
    topic_tags: list[str],
    language: LanguageCode,
    quality_score: float | None,
    message: str,
    metadata: dict[str, str] | None,
    document_repository: DocumentRepositoryPort,
) -> IngestionJobResponse:
    document = DocumentMetadata(
        doc_id=doc_id,
        title=title,
        source_type=SourceType.UPLOADED,
        topic_tags=topic_tags,
        language=language,
        status=DocumentStatus.FAILED,
        created_at=datetime.now(UTC),
        quality_score=quality_score,
    )
    await document_repository.save_document(document, [], metadata=metadata)
    return IngestionJobResponse(
        doc_id=doc_id,
        status=DocumentStatus.FAILED,
        source_type=SourceType.UPLOADED,
        message=message,
        document=document,
    )


def _timestamp_chunks(chunks: list[DocumentChunk], created_at: datetime) -> list[DocumentChunk]:
    return [chunk.model_copy(update={"created_at": created_at}) for chunk in chunks]


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
    document_repository: DocumentRepositoryPort,
) -> IngestionJobResponse:
    safe_filename = filename or "document"
    doc_id = f"upload-{safe_filename}"
    fallback_title = title or safe_filename
    requested_topic_tags = _parse_topic_tags(topic_tags)
    requested_language = language

    try:
        extracted = await document_tools.extract_text_from_pdf(content, safe_filename, content_type)
    except Exception as exc:
        error_message = f"Upload failed during PDF text extraction: {exc}"
        return await _save_failed_document(
            doc_id=doc_id,
            title=fallback_title,
            topic_tags=requested_topic_tags,
            language=requested_language,
            quality_score=0.0,
            message=error_message,
            metadata=_metadata_with_error(
                {"filename": safe_filename},
                error_code="pdf_extraction_failed",
                error_message=str(exc),
            ),
            document_repository=document_repository,
        )

    cleaned = await document_tools.clean_extracted_text(extracted.text)
    tool_metadata = await document_tools.get_document_metadata(cleaned.text, safe_filename, title)

    resolved_title = title or tool_metadata.title or safe_filename
    resolved_topic_tags = requested_topic_tags or tool_metadata.topic_tags
    resolved_language = language if language != LanguageCode.AUTO else tool_metadata.language
    document_metadata = {**extracted.metadata, **tool_metadata.metadata}

    if not cleaned.text.strip():
        return await _save_failed_document(
            doc_id=doc_id,
            title=resolved_title,
            topic_tags=resolved_topic_tags,
            language=resolved_language,
            quality_score=tool_metadata.quality_score,
            message=(
                "Upload failed: no text could be extracted from the PDF. "
                "The document may be scanned or image-only."
            ),
            metadata=_metadata_with_error(
                document_metadata,
                error_code="empty_extracted_text",
                error_message="No text could be extracted from the PDF.",
            ),
            document_repository=document_repository,
        )

    created_at = datetime.now(UTC)
    document = DocumentMetadata(
        doc_id=doc_id,
        title=resolved_title,
        source_type=SourceType.UPLOADED,
        topic_tags=resolved_topic_tags,
        language=resolved_language,
        status=DocumentStatus.INDEXED,
        created_at=created_at,
        quality_score=tool_metadata.quality_score,
    )
    chunks = await retrieval_tools.chunk_document(
        doc_id=doc_id,
        title=resolved_title,
        text=cleaned.text,
        source_type=SourceType.UPLOADED,
        topic_tags=resolved_topic_tags,
        language=resolved_language,
        section=tool_metadata.section_titles[0] if tool_metadata.section_titles else None,
        quality_score=tool_metadata.quality_score,
        metadata=document_metadata,
    )
    if not chunks:
        return await _save_failed_document(
            doc_id=doc_id,
            title=resolved_title,
            topic_tags=resolved_topic_tags,
            language=resolved_language,
            quality_score=tool_metadata.quality_score,
            message="Upload failed: the document did not produce retrieval chunks.",
            metadata=_metadata_with_error(
                document_metadata,
                error_code="empty_chunk_set",
                error_message="The retrieval chunker returned no chunks.",
            ),
            document_repository=document_repository,
        )

    chunks = _timestamp_chunks(chunks, created_at)
    upsert_result = await retrieval_tools.upsert_chunks(chunks)
    if upsert_result.inserted_count + upsert_result.updated_count == 0:
        return await _save_failed_document(
            doc_id=doc_id,
            title=resolved_title,
            topic_tags=resolved_topic_tags,
            language=resolved_language,
            quality_score=tool_metadata.quality_score,
            message="Upload failed: no chunks were inserted or updated in the retrieval index.",
            metadata=_metadata_with_error(
                document_metadata,
                error_code="index_upsert_empty",
                error_message="Retrieval index reported zero inserted and zero updated chunks.",
            ),
            document_repository=document_repository,
        )

    await document_repository.save_document(
        document,
        chunks,
        metadata=document_metadata,
    )
    return IngestionJobResponse(
        doc_id=doc_id,
        status=DocumentStatus.INDEXED,
        source_type=SourceType.UPLOADED,
        message=(
            "Upload accepted and processed. "
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
