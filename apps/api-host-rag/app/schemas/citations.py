from pydantic import BaseModel, Field


class Citation(BaseModel):
    doc_id: str
    title: str
    chunk_id: str
    snippet: str
    section: str | None = None
    score: float | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class CitationMap(BaseModel):
    citations: list[Citation] = Field(default_factory=list)

