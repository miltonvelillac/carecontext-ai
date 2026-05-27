"""Mock LLM provider adapter for deterministic development and tests."""

import json

from app.ports.llm import LlmRequest, LlmResponse


class MockLlmProvider:
    async def generate(self, request: LlmRequest) -> LlmResponse:
        if request.system_prompt and "safety classifier" in request.system_prompt.lower():
            return LlmResponse(text=json.dumps(_classify_safety(request.prompt)), model="mock-llm")

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


def _classify_safety(prompt: str) -> dict[str, object]:
    normalized_prompt = prompt.lower()
    if any(term in normalized_prompt for term in ("kill myself", "suicide", "suicidio", "matarme")):
        return {
            "risk_level": "crisis",
            "action": "redirect",
            "disclaimer": "Educational information only. Not medical advice.",
            "reasons": ["mock_crisis_match"],
            "escalation_message": (
                "I cannot safely answer this request. If this may involve immediate danger, "
                "contact emergency services now."
            ),
        }
    if any(term in normalized_prompt for term in ("medication", "dose", "diagnosis", "dosis")):
        return {
            "risk_level": "medium",
            "action": "caveat",
            "disclaimer": (
                "Educational information only. This is not a diagnosis or treatment plan. "
                "For personal medical decisions, consult a qualified health professional."
            ),
            "reasons": ["mock_sensitive_medical_match"],
            "escalation_message": None,
        }
    return {
        "risk_level": "low",
        "action": "allow",
        "disclaimer": "Educational information only. Not medical advice.",
        "reasons": [],
        "escalation_message": None,
    }
