from __future__ import annotations

from typing import Any

from carecontext_contracts.common import LanguageCode
from carecontext_contracts.retrieval_mcp import RetrievalFilter, RetrievedChunk
from embeddings import tokenize_text


class HybridChunkRetriever:
    """Rank Chroma candidates with metadata filters, hybrid scoring, and thresholds.

    Chroma returns candidates by vector distance. This class owns the app-specific
    retrieval behavior that happens after that first vector search: metadata
    filtering, vector-plus-keyword scoring, and optional minimum score thresholds.
    """

    def rank(
        self,
        candidates: list[dict[str, Any]],
        query: str,
        filters: RetrievalFilter | None,
    ) -> list[RetrievedChunk]:
        """Convert raw Chroma candidates into sorted chunks ready for answer context."""

        filtered = [
            candidate
            for candidate in candidates
            if self.metadata_matches_filter(candidate["metadata"], filters)
        ]
        ranked = sorted(
            (self.to_retrieved_chunk(candidate, query) for candidate in filtered),
            key=lambda chunk: chunk.score,
            reverse=True,
        )
        return self.apply_min_score_threshold(ranked, filters)

    def apply_min_score_threshold(
        self,
        ranked_chunks: list[RetrievedChunk],
        filters: RetrievalFilter | None,
    ) -> list[RetrievedChunk]:
        """Remove chunks below the configured minimum score, when one is provided."""

        if filters is None or filters.min_score is None:
            return ranked_chunks

        # Optional similarity threshold: return fewer than top_k rather than
        # padding the context with weakly related chunks.
        return [
            chunk
            for chunk in ranked_chunks
            if chunk.score >= filters.min_score
        ]

    def metadata_matches_filter(
        self,
        metadata: dict[str, Any],
        filters: RetrievalFilter | None,
    ) -> bool:
        """Return whether a candidate's metadata satisfies retrieval filters."""

        if filters is None:
            return True
        if filters.language != LanguageCode.AUTO and metadata.get("language") != str(filters.language):
            return False
        if filters.source_types and metadata.get("source_type") not in {
            str(source_type) for source_type in filters.source_types
        }:
            return False
        if filters.topic_tags:
            indexed_tags = {
                tag.strip()
                for tag in str(metadata.get("topic_tags", "")).split(",")
                if tag
            }
            if indexed_tags.isdisjoint(set(filters.topic_tags)):
                return False
        return True

    def to_retrieved_chunk(self, candidate: dict[str, Any], query: str) -> RetrievedChunk:
        """Build the public retrieved chunk shape and assign the hybrid score."""

        metadata = candidate["metadata"]
        document = candidate["document"]
        vector_score = max(0.0, 1.0 - float(candidate["distance"]))
        score = self.hybrid_score(document, query, vector_score)
        return RetrievedChunk(
            doc_id=str(metadata.get("doc_id", "")),
            chunk_id=str(metadata.get("chunk_id") or candidate["chunk_id"]),
            title=str(metadata.get("title", "Untitled")),
            snippet=_snippet(document),
            score=round(score, 4),
            section=metadata.get("section"),
            metadata=_public_metadata(metadata),
        )

    @staticmethod
    def hybrid_score(text: str, query: str, vector_score: float) -> float:
        """Combine vector similarity with lightweight lexical overlap."""

        return (0.75 * vector_score) + (0.25 * HybridChunkRetriever.keyword_overlap(text, query))

    @staticmethod
    def keyword_overlap(text: str, query: str) -> float:
        """Measure how many normalized query terms appear in the candidate text."""

        query_terms = set(tokenize_text(query))
        if not query_terms:
            return 0.0
        text_terms = set(tokenize_text(text))
        return len(query_terms & text_terms) / len(query_terms)


def _public_metadata(metadata: dict[str, Any]) -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in metadata.items()
        if key not in {"doc_id", "chunk_id", "title", "section"} and value is not None
    }


def _snippet(text: str, max_length: int = 500) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_length:
        return compact
    return compact[: max_length - 3].rstrip() + "..."
