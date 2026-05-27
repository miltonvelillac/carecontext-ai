import pytest

from app.ports.retrieval_tools import RetrievalFilter, RetrievedChunk
from app.schemas.query import TextQueryRequest
from app.schemas.safety import SafetyAction, SafetyAssessment, SafetyRiskLevel
from app.services.query_service import answer_text_query


class FakeRetrievalTools:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, RetrievalFilter | None]] = []

    async def retrieve_chunks(
        self,
        query: str,
        top_k: int,
        filters: RetrievalFilter | None = None,
    ) -> list[RetrievedChunk]:
        self.calls.append((query, top_k, filters))
        return [
            RetrievedChunk(
                doc_id="doc-1",
                chunk_id="doc-1-chunk-001",
                title="Sleep Basics",
                snippet="Consistent sleep routines can support sleep quality.",
                score=0.9,
                section="Sleep routines",
                metadata={"source_type": "curated"},
            )
        ]


class FakeSafetyClassifier:
    def __init__(self, safety: SafetyAssessment) -> None:
        self.safety = safety
        self.queries: list[str] = []

    async def classify(self, query: str) -> SafetyAssessment:
        self.queries.append(query)
        return self.safety


class CapturingAnswerSynthesizer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[RetrievedChunk]]] = []

    async def synthesize(
        self,
        *,
        query: str,
        language,
        retrieved_chunks: list[RetrievedChunk],
    ) -> str:
        del language
        self.calls.append((query, retrieved_chunks))
        return "Synthesized grounded answer."


def _low_safety() -> SafetyAssessment:
    return SafetyAssessment(risk_level=SafetyRiskLevel.LOW, action=SafetyAction.ALLOW)


def _caveat_safety() -> SafetyAssessment:
    return SafetyAssessment(
        risk_level=SafetyRiskLevel.MEDIUM,
        action=SafetyAction.CAVEAT,
        disclaimer=(
            "Educational information only. This is not a diagnosis or treatment plan. "
            "For personal medical decisions, consult a qualified health professional."
        ),
        reasons=["medication"],
    )


def _crisis_safety() -> SafetyAssessment:
    return SafetyAssessment(
        risk_level=SafetyRiskLevel.CRISIS,
        action=SafetyAction.REDIRECT,
        reasons=["self_harm"],
        escalation_message="Call emergency services now.",
    )


@pytest.mark.asyncio
async def test_answer_text_query_uses_synthesizer_with_retrieved_chunks() -> None:
    retrieval_tools = FakeRetrievalTools()
    safety_classifier = FakeSafetyClassifier(_low_safety())
    answer_synthesizer = CapturingAnswerSynthesizer()

    response = await answer_text_query(
        TextQueryRequest(query="How can sleep routines help?", top_k=3),
        retrieval_tools,
        safety_classifier,
        answer_synthesizer,
    )

    assert response.answer == "Synthesized grounded answer."
    assert response.safety.risk_level == "low"
    assert len(retrieval_tools.calls) == 1
    assert response.citations[0].chunk_id == "doc-1-chunk-001"
    assert len(answer_synthesizer.calls) == 1
    assert answer_synthesizer.calls[0][0] == "How can sleep routines help?"
    assert answer_synthesizer.calls[0][1][0].chunk_id == "doc-1-chunk-001"


@pytest.mark.asyncio
async def test_answer_text_query_adds_caveat_for_sensitive_medical_query() -> None:
    response = await answer_text_query(
        TextQueryRequest(query="Should I take medication for anxiety?", top_k=3),
        FakeRetrievalTools(),
        FakeSafetyClassifier(_caveat_safety()),
        CapturingAnswerSynthesizer(),
    )

    assert response.safety.risk_level == "medium"
    assert response.safety.action == "caveat"
    assert "not a diagnosis or treatment plan" in response.answer.lower()
    assert response.answer.endswith("Synthesized grounded answer.")


@pytest.mark.asyncio
async def test_answer_text_query_redirects_crisis_without_retrieval_or_synthesis() -> None:
    retrieval_tools = FakeRetrievalTools()
    answer_synthesizer = CapturingAnswerSynthesizer()

    response = await answer_text_query(
        TextQueryRequest(query="I want to kill myself", top_k=3),
        retrieval_tools,
        FakeSafetyClassifier(_crisis_safety()),
        answer_synthesizer,
    )

    assert response.safety.risk_level == "crisis"
    assert response.safety.action == "redirect"
    assert response.safety.escalation_message is not None
    assert "call emergency services" in response.answer.lower()
    assert response.citations == []
    assert response.retrieved_context == []
    assert retrieval_tools.calls == []
    assert answer_synthesizer.calls == []


@pytest.mark.asyncio
async def test_answer_text_query_delegates_empty_retrieval_response_to_synthesizer() -> None:
    class EmptyRetrievalTools:
        async def retrieve_chunks(
            self,
            query: str,
            top_k: int,
            filters: RetrievalFilter | None = None,
        ) -> list[RetrievedChunk]:
            return []

    response = await answer_text_query(
        TextQueryRequest(query="What helps stress?", top_k=3),
        EmptyRetrievalTools(),
        FakeSafetyClassifier(_low_safety()),
        CapturingAnswerSynthesizer(),
    )

    assert response.answer == "Synthesized grounded answer."
    assert response.citations == []
