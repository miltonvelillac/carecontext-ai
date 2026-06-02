from __future__ import annotations

from typing import Any

from carecontext_contracts.retrieval_mcp import RetrievalDocumentChunk, UpsertChunksResult
from ports.embeddings import EmbeddingsProviderPort
from ports.vector_store import VectorStorePort


class IndexingService:
    """Index retrieval chunks in the vector store."""

    def __init__(
        self,
        *,
        vector_store: VectorStorePort,
        embeddings_provider: EmbeddingsProviderPort,
    ) -> None:
        self.vector_store = vector_store
        self.embeddings_provider = embeddings_provider

    def upsert_chunks(self, chunks: list[RetrievalDocumentChunk]) -> UpsertChunksResult:
        """Insert or update chunks after computing their embeddings."""

        normalized_chunks = _normalize_chunks(chunks)
        if not normalized_chunks:
            return UpsertChunksResult(
                inserted_count=0,
                skipped_count=0,
                collection_name=self.vector_store.collection_name,
            )

        chunk_by_id = {chunk.chunk_id: chunk for chunk in normalized_chunks if chunk.text.strip()}
        skipped_count = len(normalized_chunks) - len(chunk_by_id)
        if not chunk_by_id:
            return UpsertChunksResult(
                inserted_count=0,
                skipped_count=skipped_count,
                collection_name=self.vector_store.collection_name,
            )

        ids = list(chunk_by_id)
        existing_ids = self.vector_store.existing_ids(ids)
        chunks_to_write = list(chunk_by_id.values())
        self.vector_store.upsert_chunks(
            chunks_to_write,
            [self.embeddings_provider.embed_text(chunk.text) for chunk in chunks_to_write],
        )

        updated_count = len(existing_ids)
        inserted_count = len(ids) - updated_count
        return UpsertChunksResult(
            inserted_count=inserted_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            collection_name=self.vector_store.collection_name,
        )


def _normalize_chunks(
    chunks: list[dict[str, Any]] | list[RetrievalDocumentChunk],
) -> list[RetrievalDocumentChunk]:
    return [
        chunk
        if isinstance(chunk, RetrievalDocumentChunk)
        else RetrievalDocumentChunk.model_validate(chunk)
        for chunk in chunks
    ]
