from typing import Protocol

from pydantic import BaseModel


class LlmRequest(BaseModel):
    prompt: str
    system_prompt: str | None = None
    language: str = "auto"


class LlmResponse(BaseModel):
    text: str
    model: str | None = None


class LlmProvider(Protocol):
    """Strategy port for text generation providers.

    Strategy Pattern: OpenAI, mock, or future local/cloud LLM providers can
    implement this same interface without changing query orchestration code.
    """

    async def generate(self, request: LlmRequest) -> LlmResponse:
        ...
