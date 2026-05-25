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
    async def generate(self, request: LlmRequest) -> LlmResponse:
        ...

