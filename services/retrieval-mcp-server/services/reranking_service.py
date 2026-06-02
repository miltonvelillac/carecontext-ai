from __future__ import annotations

from carecontext_contracts.retrieval_mcp import (
    RerankResultsResult,
    RerankedChunk,
    RetrievedChunk,
)
from services.retrievers import HybridChunkRetriever


class RerankingService:
    """Rerank already retrieved chunks with the configured ranking logic."""

    def __init__(self, *, retriever: HybridChunkRetriever) -> None:
        self.retriever = retriever

    def rerank_results(
        self,
        query: str,
        results: list[RetrievedChunk],
        top_k: int,
    ) -> RerankResultsResult:
        """Rerank retrieved chunks and keep the top requested items."""

        if top_k <= 0:
            return RerankResultsResult()

        normalized_results = [
            result if isinstance(result, RetrievedChunk) else RetrievedChunk.model_validate(result)
            for result in results
        ]
        reranked = sorted(
            (
                RerankedChunk(
                    chunk=result,
                    rerank_score=self.retriever.hybrid_score(
                        result.snippet,
                        query,
                        result.score,
                    ),
                    reason="vector_score_plus_keyword_overlap",
                )
                for result in normalized_results
            ),
            key=lambda item: item.rerank_score,
            reverse=True,
        )
        return RerankResultsResult(results=reranked[:top_k])
