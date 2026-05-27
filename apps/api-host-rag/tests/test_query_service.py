import pytest

from app.ports.llm import LlmRequest, LlmResponse
from app.ports.retrieval_tools import RetrievalFilter, RetrievedChunk
from app.schemas.query import TextQueryRequest
from app.services.query_service import answer_text_query


class FakeRetrievalTools:
    async def retrieve_chunks(
        self,
        query: str,
        top_k: int,
        filters: RetrievalFilter | None = None,
    ) -> list[RetrievedChunk]:
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
        return LlmResponse(text="LLM grounded answer.", model="test-llm")


@pytest.mark.asyncio
async def test_answer_text_query_uses_llm_with_retrieved_context() -> None:
    llm_provider = CapturingLlmProvider()

    response = await answer_text_query(
        TextQueryRequest(query="How can sleep routines help?", top_k=3),
        FakeRetrievalTools(),
        llm_provider,
    )

    assert response.answer == "LLM grounded answer."
    assert response.citations[0].chunk_id == "doc-1-chunk-001"
    assert len(llm_provider.requests) == 1
    assert "Retrieved context:" in llm_provider.requests[0].prompt
    assert "Consistent sleep routines" in llm_provider.requests[0].prompt
    assert "How can sleep routines help?" in llm_provider.requests[0].prompt


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
    assert llm_provider.requests == []
