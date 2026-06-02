from __future__ import annotations

from typing import Any

from carecontext_contracts.common import LanguageCode
from carecontext_contracts.retrieval_mcp import (
    HybridSearchResult,
    RetrievalFilter,
)
from core.settings import RetrievalSettings
from ports.embeddings import EmbeddingsProviderPort
from ports.vector_store import VectorStorePort
from services.retrievers import HybridChunkRetriever


class RetrievalService:
    """Search indexed chunks with vector search plus app-specific ranking."""

    def __init__(
        self,
        *,
        settings: RetrievalSettings,
        vector_store: VectorStorePort,
        embeddings_provider: EmbeddingsProviderPort,
        retriever: HybridChunkRetriever,
    ) -> None:
        self.settings = settings
        self.vector_store = vector_store
        self.embeddings_provider = embeddings_provider
        self.retriever = retriever

    def search_chunks(
        self,
        query: str,
        top_k: int,
        filters: RetrievalFilter | None = None,
    ) -> HybridSearchResult:
        """Search indexed chunks and return the best retrieval candidates for a query."""

        # Guard clause: empty queries or non-positive limits should not hit Chroma.
        if not query.strip() or top_k <= 0:
            return HybridSearchResult()

        # Check the vector store before building embeddings or querying.
        collection_size = self.vector_store.count()
        if collection_size == 0:
            return HybridSearchResult()

        # Normalize dict filters into the shared contract model so downstream code
        # can read language, metadata filters, and min_score consistently.
        retrieval_filter = _normalize_filter(filters)

        # Ask Chroma for a candidate pool larger than top_k. Chroma ranks these by
        # vector distance only; the app reranks them later with hybrid scoring.
        n_results = min(collection_size, top_k * self.settings.candidate_multiplier)
        candidates = self.vector_store.query_chunks(
            query_embedding=self.embeddings_provider.embed_text(query),
            n_results=n_results,
            where=_chroma_where_filter(retrieval_filter),
        )

        # Apply metadata filters, compute hybrid scores, sort by relevance, and
        # apply the optional min_score threshold.
        ranked = self.retriever.rank(candidates, query, retrieval_filter)

        # Return at most top_k chunks after reranking and threshold filtering.
        return HybridSearchResult(results=ranked[:top_k])


def _normalize_filter(filters: dict[str, Any] | RetrievalFilter | None) -> RetrievalFilter | None:
    if filters is None:
        return None
    return filters if isinstance(filters, RetrievalFilter) else RetrievalFilter.model_validate(filters)


def _chroma_where_filter(filters: RetrievalFilter | None) -> dict[str, Any] | None:
    """Build Chroma-native metadata filters for exact-match fields.

    Topic tags stay in the post-query retriever filter because they are stored as
    comma-separated metadata strings, not as native Chroma arrays.
    """

    if filters is None:
        return None

    conditions: list[dict[str, Any]] = []
    if filters.language != LanguageCode.AUTO:
        conditions.append({"language": filters.language.value})
    if len(filters.source_types) == 1:
        conditions.append({"source_type": filters.source_types[0].value})
    elif len(filters.source_types) > 1:
        conditions.append(
            {
                "source_type": {
                    "$in": [source_type.value for source_type in filters.source_types]
                }
            }
        )

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}
