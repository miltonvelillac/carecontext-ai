import pytest
from pydantic import BaseModel

from app.ports.llm import LlmRequest, LlmResponse
from app.ports.retrieval_tools import RetrievalFilter, RetrievedChunk
from app.schemas.query import TextQueryRequest
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


class CapturingLlmProvider:
    def __init__(self) -> None:
        self.requests: list[LlmRequest] = []

    async def generate(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        if request.system_prompt and "safety classifier" in request.system_prompt.lower():
            return LlmResponse(text=_safety_response_for_prompt(request.prompt), model="test-llm")
        return LlmResponse(text="LLM grounded answer.", model="test-llm")


@pytest.mark.asyncio
async def test_answer_text_query_uses_llm_with_retrieved_context() -> None:
    llm_provider = CapturingLlmProvider()
    retrieval_tools = FakeRetrievalTools()

    response = await answer_text_query(
        TextQueryRequest(query="How can sleep routines help?", top_k=3),
        retrieval_tools,
        llm_provider,
    )

    assert response.answer == "LLM grounded answer."
    assert response.safety.risk_level == "low"
    assert len(retrieval_tools.calls) == 1
    assert response.citations[0].chunk_id == "doc-1-chunk-001"
    assert len(llm_provider.requests) == 2
    assert "Retrieved context:" in llm_provider.requests[1].prompt
    assert "Consistent sleep routines" in llm_provider.requests[1].prompt
    assert "How can sleep routines help?" in llm_provider.requests[1].prompt


@pytest.mark.asyncio
async def test_answer_text_query_adds_caveat_for_sensitive_medical_query() -> None:
    llm_provider = CapturingLlmProvider()

    response = await answer_text_query(
        TextQueryRequest(query="Should I take medication for anxiety?", top_k=3),
        FakeRetrievalTools(),
        llm_provider,
    )

    assert response.safety.risk_level == "medium"
    assert response.safety.action == "caveat"
    assert "not a diagnosis or treatment plan" in response.answer.lower()
    assert response.answer.endswith("LLM grounded answer.")
    assert len(llm_provider.requests) == 2


@pytest.mark.asyncio
async def test_answer_text_query_redirects_crisis_without_retrieval_or_llm() -> None:
    llm_provider = CapturingLlmProvider()
    retrieval_tools = FakeRetrievalTools()

    response = await answer_text_query(
        TextQueryRequest(query="I want to kill myself", top_k=3),
        retrieval_tools,
        llm_provider,
    )

    assert response.safety.risk_level == "crisis"
    assert response.safety.action == "redirect"
    assert response.safety.escalation_message is not None
    assert "call emergency services" in response.answer.lower()
    assert response.citations == []
    assert response.retrieved_context == []
    assert retrieval_tools.calls == []
    assert len(llm_provider.requests) == 1


@pytest.mark.asyncio
async def test_answer_text_query_does_not_call_llm_without_results() -> None:
    class EmptyRetrievalTools:
        async def retrieve_chunks(
            self,
            query: str,
            top_k: int,
            filters: RetrievalFilter | None = None,
        ) -> list[RetrievedChunk]:
            return []

    llm_provider = CapturingLlmProvider()

    response = await answer_text_query(
        TextQueryRequest(query="What helps stress?", top_k=3),
        EmptyRetrievalTools(),
        llm_provider,
    )

    assert "could not find relevant context" in response.answer.lower()
    assert len(llm_provider.requests) == 1


def _safety_response_for_prompt(prompt: str) -> str:
    normalized_query = prompt.split("User query:", maxsplit=1)[-1].lower()
    if "kill myself" in normalized_query:
        return SafetyPayload(
            risk_level="crisis",
            action="redirect",
            disclaimer="Educational information only. Not medical advice.",
            reasons=["self_harm"],
            escalation_message="Call emergency services now.",
        ).model_dump_json()
    if "medication" in normalized_query:
        return SafetyPayload(
            risk_level="medium",
            action="caveat",
            disclaimer=(
                "Educational information only. This is not a diagnosis or treatment plan. "
                "For personal medical decisions, consult a qualified health professional."
            ),
            reasons=["medication"],
            escalation_message=None,
        ).model_dump_json()
    return SafetyPayload(
        risk_level="low",
        action="allow",
        disclaimer="Educational information only. Not medical advice.",
        reasons=[],
        escalation_message=None,
    ).model_dump_json()


class SafetyPayload(BaseModel):
    risk_level: str
    action: str
    disclaimer: str
    reasons: list[str]
    escalation_message: str | None
