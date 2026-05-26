from carecontext_contracts.common import MetadataKey, MetadataValue

from app.schemas.common import DocumentStatus, LanguageCode, SourceType
from app.schemas.documents import DocumentChunk, DocumentSummary

MOCK_DOCUMENT = DocumentSummary(
    doc_id="curated-sleep-basics",
    title="Sleep Hygiene Basics",
    source_type=SourceType.CURATED,
    language=LanguageCode.EN,
    status=DocumentStatus.INDEXED,
    topic_tags=["sleep", "stress"],
    chunk_count=1,
)

MOCK_CHUNK = DocumentChunk(
    doc_id=MOCK_DOCUMENT.doc_id,
    chunk_id="curated-sleep-basics-chunk-001",
    title=MOCK_DOCUMENT.title,
    text=(
        "Consistent sleep routines, reduced evening stimulation, and regular wake times "
        "can support sleep quality and may help people manage stress."
    ),
    source_type=MOCK_DOCUMENT.source_type,
    topic_tags=MOCK_DOCUMENT.topic_tags,
    language=MOCK_DOCUMENT.language,
    section="Sleep routines",
    metadata={MetadataKey.MOCK: MetadataValue.TRUE},
)


def list_mock_documents() -> list[DocumentSummary]:
    return [MOCK_DOCUMENT]


def list_mock_chunks(doc_id: str) -> list[DocumentChunk]:
    if doc_id != MOCK_DOCUMENT.doc_id:
        return []
    return [MOCK_CHUNK]

