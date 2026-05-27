import pytest

from app.ports.llm import LlmRequest, LlmResponse
from app.chains.langchain_safety_classifier import LangChainSafetyClassifier


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

    safety = await LangChainSafetyClassifier(llm_provider).classify(
        "How can sleep routines help with stress?"
    )

    assert safety.risk_level == "low"
    assert safety.action == "allow"
    assert safety.reasons == []
    assert len(llm_provider.requests) == 1
    assert "User query: How can sleep routines help with stress?" in llm_provider.requests[0].prompt


@pytest.mark.asyncio
async def test_classify_query_safety_redirects_crisis_intent() -> None:
    llm_provider = StaticSafetyLlmProvider(
        """
        {
          "risk_level": "crisis",
          "action": "redirect",
          "disclaimer": "Educational information only. Not medical advice.",
          "reasons": ["self_harm"],
          "escalation_message": "Call emergency services now."
        }
        """
    )
    safety = await LangChainSafetyClassifier(llm_provider).classify(
        "No quiero vivir y quiero hacerme dano",
    )

    assert safety.risk_level == "crisis"
    assert safety.action == "redirect"
    assert safety.escalation_message is not None
    assert safety.reasons


@pytest.mark.asyncio
async def test_classify_query_safety_caveats_sensitive_medical_question() -> None:
    llm_provider = StaticSafetyLlmProvider(
        """
        {
          "risk_level": "medium",
          "action": "caveat",
          "disclaimer": "Educational information only. Not medical advice.",
          "reasons": ["medication_dosage"],
          "escalation_message": null
        }
        """
    )
    safety = await LangChainSafetyClassifier(llm_provider).classify(
        "Debo tomar una dosis de medicamento para dormir?",
    )

    assert safety.risk_level == "medium"
    assert safety.action == "caveat"
    assert "not a diagnosis" in safety.disclaimer.lower()


@pytest.mark.asyncio
async def test_classify_query_safety_fails_closed_when_llm_returns_invalid_json() -> None:
    safety = await LangChainSafetyClassifier(StaticSafetyLlmProvider("not json")).classify(
        "How can sleep routines help?"
    )

    assert safety.risk_level == "high"
    assert safety.action == "redirect"
    assert safety.reasons == ["safety_classifier_failed"]
