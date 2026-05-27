import pytest

from app.ports.llm import LlmRequest, LlmResponse
from app.services.safety_service import classify_query_safety


class StaticSafetyLlmProvider:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.requests: list[LlmRequest] = []

    async def generate(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        return LlmResponse(text=self.response_text, model="test-safety-llm")


@pytest.mark.asyncio
async def test_classify_query_safety_allows_normal_educational_query() -> None:
    llm_provider = StaticSafetyLlmProvider(
        """
        {
          "risk_level": "low",
          "action": "allow",
          "disclaimer": "Educational information only. Not medical advice.",
          "reasons": [],
          "escalation_message": null
        }
        """
    )

    safety = await classify_query_safety("How can sleep routines help with stress?", llm_provider)

    assert safety.risk_level == "low"
    assert safety.action == "allow"
    assert safety.reasons == []
    assert len(llm_provider.requests) == 1
    assert "User query: How can sleep routines help with stress?" in llm_provider.requests[0].prompt


@pytest.mark.asyncio
async def test_classify_query_safety_redirects_crisis_intent() -> None:
    safety = await classify_query_safety(
        "No quiero vivir y quiero hacerme dano",
        StaticSafetyLlmProvider(
            """
            {
              "risk_level": "crisis",
              "action": "redirect",
              "disclaimer": "Educational information only. Not medical advice.",
              "reasons": ["self_harm"],
              "escalation_message": "Call emergency services now."
            }
            """
        ),
    )

    assert safety.risk_level == "crisis"
    assert safety.action == "redirect"
    assert safety.escalation_message is not None
    assert safety.reasons


@pytest.mark.asyncio
async def test_classify_query_safety_caveats_sensitive_medical_question() -> None:
    safety = await classify_query_safety(
        "Debo tomar una dosis de medicamento para dormir?",
        StaticSafetyLlmProvider(
            """
            {
              "risk_level": "medium",
              "action": "caveat",
              "disclaimer": "Educational information only. Not medical advice.",
              "reasons": ["medication_dosage"],
              "escalation_message": null
            }
            """
        ),
    )

    assert safety.risk_level == "medium"
    assert safety.action == "caveat"
    assert "not a diagnosis" in safety.disclaimer.lower()


@pytest.mark.asyncio
async def test_classify_query_safety_fails_closed_when_llm_returns_invalid_json() -> None:
    safety = await classify_query_safety(
        "How can sleep routines help?",
        StaticSafetyLlmProvider("not json"),
    )

    assert safety.risk_level == "high"
    assert safety.action == "redirect"
    assert safety.reasons == ["safety_classifier_failed"]
