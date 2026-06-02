from __future__ import annotations

import os
from dataclasses import dataclass

from carecontext_contracts.common import ChromaHnswSpace
from carecontext_contracts.retrieval_mcp import RetrievalEmbeddingsProvider

DEFAULT_COLLECTION_NAME = "carecontext_chunks"
DEFAULT_CANDIDATE_MULTIPLIER = 5
DEFAULT_EMBEDDING_DIMENSIONS = 384
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"


@dataclass(frozen=True)
class RetrievalSettings:
    """Configuration object for the Retrieval MCP server."""

    collection_name: str = DEFAULT_COLLECTION_NAME
    chroma_host: str | None = None
    chroma_port: int = 8000
    chroma_path: str = "./data/chroma"
    chroma_hnsw_space: ChromaHnswSpace = ChromaHnswSpace.COSINE
    candidate_multiplier: int = DEFAULT_CANDIDATE_MULTIPLIER
    embeddings_provider: RetrievalEmbeddingsProvider = RetrievalEmbeddingsProvider.DETERMINISTIC
    embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
    openai_api_key: str | None = None
    openai_embedding_model: str = DEFAULT_OPENAI_EMBEDDING_MODEL

    @classmethod
    def from_env(cls) -> RetrievalSettings:
        """Build settings from environment variables passed by the MCP host."""

        return cls(
            collection_name=os.getenv("CARECONTEXT_CHROMA_COLLECTION", DEFAULT_COLLECTION_NAME),
            chroma_host=os.getenv("CARECONTEXT_CHROMA_HOST") or None,
            chroma_port=int(os.getenv("CARECONTEXT_CHROMA_PORT", "8000")),
            chroma_path=os.getenv("CARECONTEXT_CHROMA_PATH", "./data/chroma"),
            chroma_hnsw_space=ChromaHnswSpace(
                os.getenv("CARECONTEXT_CHROMA_HNSW_SPACE", ChromaHnswSpace.COSINE.value)
            ),
            candidate_multiplier=max(
                1,
                int(
                    os.getenv(
                        "CARECONTEXT_RETRIEVAL_CANDIDATE_MULTIPLIER",
                        str(DEFAULT_CANDIDATE_MULTIPLIER),
                    )
                ),
            ),
            embeddings_provider=RetrievalEmbeddingsProvider(
                os.getenv(
                    "CARECONTEXT_EMBEDDINGS_PROVIDER",
                    RetrievalEmbeddingsProvider.DETERMINISTIC.value,
                ).lower()
            ),
            embedding_dimensions=int(
                os.getenv("CARECONTEXT_EMBEDDING_DIMENSIONS", str(DEFAULT_EMBEDDING_DIMENSIONS))
            ),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_embedding_model=os.getenv(
                "OPENAI_EMBEDDING_MODEL",
                DEFAULT_OPENAI_EMBEDDING_MODEL,
            ),
        )
