"""Mock LLM provider adapter for deterministic development and tests."""

from app.ports.llm import LlmRequest, LlmResponse


class MockLlmProvider:
    async def generate(self, request: LlmRequest) -> LlmResponse:
        context = _extract_context(request.prompt)
        if not context:
            return LlmResponse(
                text=(
                    "I could not find relevant context in the indexed documents for this "
                    "question. This assistant is educational and not a substitute for "
                    "professional care."
                ),
                model="mock-llm",
            )
        return LlmResponse(
            text=(
                "Based on the retrieved educational sources: "
                f"{context} "
                "This response is educational and not medical advice."
            ),
            model="mock-llm",
        )


def _extract_context(prompt: str) -> str:
    marker = "Retrieved context:"
    if marker not in prompt:
        return ""
    context = prompt.split(marker, maxsplit=1)[1]
    context = context.split("Question:", maxsplit=1)[0]
    return " ".join(context.split()).strip()
