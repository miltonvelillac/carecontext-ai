from __future__ import annotations

from typing import Any

import chromadb
from carecontext_contracts.retrieval_mcp import RetrievalDocumentChunk
from core.settings import RetrievalSettings


class ChromaVectorStoreAdapter:
    """ChromaDB adapter that implements the vector store port."""

    def __init__(self, settings: RetrievalSettings) -> None:
        self.settings = settings
        self._client: Any | None = None
        self._collection: Any | None = None

    @property
    def collection_name(self) -> str:
        """Return the configured Chroma collection name."""

        return self.settings.collection_name

    def count(self) -> int:
        """Return how many chunks are indexed in the Chroma collection."""

        return self._get_collection().count()

    def existing_ids(self, ids: list[str]) -> set[str]:
        """Return ids that already exist in Chroma."""

        try:
            existing = self._get_collection().get(ids=ids, include=[])
        except Exception:
            return set()
        return set(existing.get("ids", []))

    def upsert_chunks(
        self,
        chunks: list[RetrievalDocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Insert or update chunks using caller-provided embeddings."""

        self._get_collection().upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[_chunk_metadata(chunk) for chunk in chunks],
        )

    def query_chunks(
        self,
        *,
        query_embedding: list[float],
        n_results: int,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query Chroma and normalize its column-oriented response."""

        query_arguments: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_arguments["where"] = where

        return _query_candidates(self._get_collection().query(**query_arguments))

    def list_chunks(
        self,
        *,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Return stored chunks without vector ranking for lexical fallback."""

        get_arguments: dict[str, Any] = {
            "include": ["documents", "metadatas"],
        }
        if where:
            get_arguments["where"] = where

        return _get_candidates(self._get_collection().get(**get_arguments))

    def _get_collection(self) -> Any:
        if self._collection is None:
            self._collection = self._get_client().get_or_create_collection(
                name=self.settings.collection_name,
                metadata={"hnsw:space": self.settings.chroma_hnsw_space.value},
                embedding_function=None,
            )
        return self._collection

    def _get_client(self) -> Any:
        if self._client is None:
            if self.settings.chroma_host:
                self._client = chromadb.HttpClient(
                    host=self.settings.chroma_host,
                    port=self.settings.chroma_port,
                )
            else:
                self._client = chromadb.PersistentClient(path=self.settings.chroma_path)
        return self._client


def _chunk_metadata(chunk: RetrievalDocumentChunk) -> dict[str, str | int | float | bool]:
    metadata: dict[str, str | int | float | bool] = {
        "doc_id": chunk.doc_id,
        "chunk_id": chunk.chunk_id,
        "title": chunk.title,
        "source_type": str(chunk.source_type),
        "topic_tags": ",".join(chunk.topic_tags),
        "language": str(chunk.language),
    }
    if chunk.section is not None:
        metadata["section"] = chunk.section
    if chunk.created_at is not None:
        metadata["created_at"] = chunk.created_at.isoformat()
    if chunk.quality_score is not None:
        metadata["quality_score"] = chunk.quality_score

    for key, value in chunk.metadata.items():
        if value is not None:
            metadata[f"custom_{key}"] = str(value)
    return metadata


def _query_candidates(raw_results: dict[str, Any]) -> list[dict[str, Any]]:
    ids = raw_results.get("ids", [[]])[0]
    documents = raw_results.get("documents", [[]])[0]
    metadatas = raw_results.get("metadatas", [[]])[0]
    distances = raw_results.get("distances", [[]])[0]
    candidates: list[dict[str, Any]] = []
    for index, chunk_id in enumerate(ids):
        candidates.append(
            {
                "chunk_id": chunk_id,
                "document": documents[index] or "",
                "metadata": metadatas[index] or {},
                "distance": distances[index],
            }
        )
    return candidates


def _get_candidates(raw_results: dict[str, Any]) -> list[dict[str, Any]]:
    ids = raw_results.get("ids", [])
    documents = raw_results.get("documents", [])
    metadatas = raw_results.get("metadatas", [])
    candidates: list[dict[str, Any]] = []
    for index, chunk_id in enumerate(ids):
        candidates.append(
            {
                "chunk_id": chunk_id,
                "document": documents[index] or "",
                "metadata": metadatas[index] or {},
                "distance": 0.0,
            }
        )
    return candidates
