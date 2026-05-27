from app.adapters.mock.corpus import MOCK_CHUNK
from app.ports.retrieval_tools import (
    RerankedChunk,
    RetrievalFilter,
    RetrievedChunk,
    UpsertChunksResult,
)
from app.schemas.common import LanguageCode, SourceType
from app.schemas.documents import DocumentChunk


class MockRetrievalTools:
    async def chunk_document(
        self,
        *,
        doc_id: str,
        title: str,
        text: str,
        source_type: SourceType,
        topic_tags: list[str],
        language: LanguageCode,
        section: str | None = None,
        quality_score: float | None = None,
        metadata: dict[str, str] | None = None,
    ) -> list[DocumentChunk]:
        return [
            DocumentChunk(
                doc_id=doc_id,
                chunk_id=f"{doc_id}-chunk-001",
                title=title,
                text=text,
                source_type=source_type,
                topic_tags=topic_tags,
                language=language,
                section=section,
                quality_score=quality_score,
                metadata=metadata or {},
            )
        ]

    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> UpsertChunksResult:
        return UpsertChunksResult(
            inserted_count=len(chunks),
            updated_count=0,
            skipped_count=0,
            collection_name="mock-carecontext",
        )

    async def hybrid_search(
        self,
        query: str,
        top_k: int,
        filters: RetrievalFilter | None = None,
    ) -> list[RetrievedChunk]:
        del query, filters
        result = RetrievedChunk(
            doc_id=MOCK_CHUNK.doc_id,
            chunk_id=MOCK_CHUNK.chunk_id,
            title=MOCK_CHUNK.title,
            snippet=MOCK_CHUNK.text,
            score=0.92,
            section=MOCK_CHUNK.section,
            metadata=MOCK_CHUNK.metadata,
        )
        return [result][:top_k]

    async def rerank_results(
        self,
        query: str,
        results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RerankedChunk]:
        del query
        return [
            RerankedChunk(chunk=result, rerank_score=result.score, reason="mock_rerank")
            for result in results[:top_k]
        ]
