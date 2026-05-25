from pydantic import BaseModel, Field

from app.schemas.audio import TextToSpeechResult, TranscriptionResult
from app.schemas.citations import Citation
from app.schemas.common import LanguageCode, SourceType
from app.schemas.safety import SafetyAssessment


class RetrievalFilter(BaseModel):
    source_types: list[SourceType] = Field(default_factory=list)
    topic_tags: list[str] = Field(default_factory=list)
    language: LanguageCode = LanguageCode.AUTO


class TextQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    language: LanguageCode = LanguageCode.AUTO
    top_k: int = Field(default=5, ge=1, le=20)
    filters: RetrievalFilter | None = None
    include_tts: bool = False


class AudioQueryRequest(BaseModel):
    language: LanguageCode = LanguageCode.AUTO
    top_k: int = Field(default=5, ge=1, le=20)
    filters: RetrievalFilter | None = None
    include_tts: bool = True


class RetrievedContextChunk(BaseModel):
    doc_id: str
    title: str
    chunk_id: str
    snippet: str
    score: float
    section: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RagAnswerResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    safety: SafetyAssessment
    retrieved_context: list[RetrievedContextChunk] = Field(default_factory=list)
    transcription: TranscriptionResult | None = None
    tts: TextToSpeechResult | None = None
    trace_id: str | None = None

