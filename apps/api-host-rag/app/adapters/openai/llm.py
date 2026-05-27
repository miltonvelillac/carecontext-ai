from typing import Any

from openai import AsyncOpenAI

from app.ports.llm import LlmRequest, LlmResponse

DEFAULT_OPENAI_LLM_MODEL = "gpt-5.2"


class OpenAiLlmProvider:
    """OpenAI Responses API implementation of the LLM provider port."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model or DEFAULT_OPENAI_LLM_MODEL
        self.client = client or AsyncOpenAI(api_key=api_key)

    async def generate(self, request: LlmRequest) -> LlmResponse:
        response = await self.client.responses.create(
            model=self.model,
            input=request.prompt,
            instructions=request.system_prompt,
        )
        return LlmResponse(text=response.output_text, model=self.model)
