import pytest

from app.adapters.openai.llm import OpenAiLlmProvider
from app.ports.llm import LlmRequest


class FakeOpenAiResponse:
    output_text = "OpenAI response text."


class FakeResponsesResource:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeOpenAiResponse()


class FakeOpenAiClient:
    def __init__(self) -> None:
        self.responses = FakeResponsesResource()


@pytest.mark.asyncio
async def test_openai_llm_provider_calls_responses_api() -> None:
    client = FakeOpenAiClient()
    provider = OpenAiLlmProvider(model="gpt-test", client=client)

    response = await provider.generate(
        LlmRequest(
            system_prompt="System instructions.",
            prompt="User prompt.",
            language="en",
        )
    )

    assert response.text == "OpenAI response text."
    assert response.model == "gpt-test"
    assert client.responses.calls == [
        {
            "model": "gpt-test",
            "input": "User prompt.",
            "instructions": "System instructions.",
        }
    ]
