from typing import Protocol

from app.ports.retrieval_tools import RetrievedChunk
from app.schemas.common import LanguageCode


class AnswerSynthesizerPort(Protocol):
    async def synthesize(
        self,
        *,
        query: str,
        language: LanguageCode,
        retrieved_chunks: list[RetrievedChunk],
    ) -> str:
        ...
