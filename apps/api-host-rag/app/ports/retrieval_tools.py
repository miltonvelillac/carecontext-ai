from typing import Protocol

from pydantic import BaseModel


class RetrievedChunk(BaseModel):
    doc_id: str
    chunk_id: str
    title: str
    snippet: str
    score: float
    metadata: dict[str, str]


class RetrievalToolsPort(Protocol):
    async def hybrid_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        ...

