from __future__ import annotations

from adapters.chroma_vector_store import ChromaVectorStoreAdapter
from adapters.embeddings import build_embeddings_provider
from adapters.text_splitter import LangChainTextSplitterAdapter
from core.settings import RetrievalSettings
from ports.embeddings import EmbeddingsProviderPort
from ports.text_splitter import TextSplitterPort
from services.chunking_service import ChunkingService
from services.indexing_service import IndexingService
from services.reranking_service import RerankingService
from services.retrieval_service import RetrievalService
from services.retrievers import HybridChunkRetriever


class RetrievalContainer:
    """Lazy-loaded composition root for the Retrieval MCP server."""

    def __init__(self, settings: RetrievalSettings | None = None) -> None:
        self.settings = settings or RetrievalSettings.from_env()
        self._embeddings_provider: EmbeddingsProviderPort | None = None
        self._text_splitter: TextSplitterPort | None = None
        self._vector_store: ChromaVectorStoreAdapter | None = None
        self._retriever: HybridChunkRetriever | None = None
        self._chunking_service: ChunkingService | None = None
        self._indexing_service: IndexingService | None = None
        self._retrieval_service: RetrievalService | None = None
        self._reranking_service: RerankingService | None = None

    @property
    def embeddings_provider(self) -> EmbeddingsProviderPort:
        """Return the configured embeddings provider, created on first use."""

        if self._embeddings_provider is None:
            self._embeddings_provider = build_embeddings_provider(self.settings)
        return self._embeddings_provider

    @property
    def text_splitter(self) -> TextSplitterPort:
        """Return the configured text splitter, created on first use."""

        if self._text_splitter is None:
            self._text_splitter = LangChainTextSplitterAdapter()
        return self._text_splitter

    @property
    def vector_store(self) -> ChromaVectorStoreAdapter:
        """Return the configured vector store adapter, created on first use."""

        if self._vector_store is None:
            self._vector_store = ChromaVectorStoreAdapter(self.settings)
        return self._vector_store

    @property
    def retriever(self) -> HybridChunkRetriever:
        """Return the chunk ranking component, created on first use."""

        if self._retriever is None:
            self._retriever = HybridChunkRetriever()
        return self._retriever

    @property
    def chunking_service(self) -> ChunkingService:
        """Return the chunking service, created on first use."""

        if self._chunking_service is None:
            self._chunking_service = ChunkingService(text_splitter=self.text_splitter)
        return self._chunking_service

    @property
    def indexing_service(self) -> IndexingService:
        """Return the indexing service with dependencies injected."""

        if self._indexing_service is None:
            self._indexing_service = IndexingService(
                vector_store=self.vector_store,
                embeddings_provider=self.embeddings_provider,
            )
        return self._indexing_service

    @property
    def retrieval_service(self) -> RetrievalService:
        """Return the retrieval service with dependencies injected."""

        if self._retrieval_service is None:
            self._retrieval_service = RetrievalService(
                settings=self.settings,
                vector_store=self.vector_store,
                embeddings_provider=self.embeddings_provider,
                retriever=self.retriever,
            )
        return self._retrieval_service

    @property
    def reranking_service(self) -> RerankingService:
        """Return the reranking service with dependencies injected."""

        if self._reranking_service is None:
            self._reranking_service = RerankingService(retriever=self.retriever)
        return self._reranking_service


_container: RetrievalContainer | None = None


def get_container() -> RetrievalContainer:
    """Return the process-wide lazy container for MCP tool calls."""

    global _container
    if _container is None:
        _container = RetrievalContainer()
    return _container
