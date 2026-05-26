from typing import Protocol

from pydantic import BaseModel, Field

from app.schemas.common import LanguageCode, SourceType
from app.schemas.documents import DocumentChunk


class RetrievedChunk(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    snippet: str
    score: float
    section: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RetrievalFilter(BaseModel):
    source_types: list[SourceType] = Field(default_factory=list)
    topic_tags: list[str] = Field(default_factory=list)
    language: LanguageCode = LanguageCode.AUTO


class UpsertChunksResult(BaseModel):
    inserted_count: int = Field(ge=0)
    updated_count: int = Field(default=0, ge=0)
    skipped_count: int = Field(default=0, ge=0)
    collection_name: str | None = None


class RerankedChunk(BaseModel):
    chunk: RetrievedChunk
    rerank_score: float
    reason: str | None = None


class RetrievalToolsPort(Protocol):
    """Port for indexing and retrieval operations.

    Strategy plus Ports and Adapters: the core RAG workflow can use this
    contract while the concrete retrieval strategy can change underneath.
    """

    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> UpsertChunksResult:
        ...

    async def hybrid_search(
        self,
        query: str,
        top_k: int,
        filters: RetrievalFilter | None = None,
    ) -> list[RetrievedChunk]:
        ...

    async def rerank_results(
        self,
        query: str,
        results: list[RetrievedChunk],
        top_k: int,
    ) -> list[RerankedChunk]:
        ...
