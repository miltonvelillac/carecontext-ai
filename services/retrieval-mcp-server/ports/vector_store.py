from __future__ import annotations

from typing import Any, Protocol

from carecontext_contracts.retrieval_mcp import RetrievalDocumentChunk


class VectorStorePort(Protocol):
    """Port for vector database operations used by retrieval services."""

    @property
    def collection_name(self) -> str:
        """Return the collection name used by the vector store."""
        ...

    def count(self) -> int:
        """Return how many chunks are indexed."""
        ...

    def existing_ids(self, ids: list[str]) -> set[str]:
        """Return ids that already exist in the store."""
        ...

    def upsert_chunks(
        self,
        chunks: list[RetrievalDocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Insert or update chunks with precomputed embeddings."""
        ...

    def query_chunks(
        self,
        *,
        query_embedding: list[float],
        n_results: int,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query chunks and return normalized candidate dictionaries."""
        ...
