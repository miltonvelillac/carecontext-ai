import pytest

from app.chains.langchain_answer_synthesizer import LangChainAnswerSynthesizer
from app.ports.llm import LlmRequest, LlmResponse
from app.ports.retrieval_tools import RetrievedChunk
from app.schemas.common import LanguageCode


class CapturingLlmProvider:
    def __init__(self) -> None:
        self.requests: list[LlmRequest] = []

    async def generate(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        return LlmResponse(text="LLM grounded answer.", model="test-llm")


@pytest.mark.asyncio
async def test_answer_synthesizer_builds_rag_prompt_with_retrieved_context() -> None:
    llm_provider = CapturingLlmProvider()
    synthesizer = LangChainAnswerSynthesizer(llm_provider)

    answer = await synthesizer.synthesize(
        query="How can sleep routines help?",
        language=LanguageCode.EN,
        retrieved_chunks=[
            RetrievedChunk(
                doc_id="doc-1",
                chunk_id="doc-1-chunk-001",
                title="Sleep Basics",
                snippet="Consistent sleep routines can support sleep quality.",
                score=0.9,
            )
        ],
    )

    assert answer == "LLM grounded answer."
    assert len(llm_provider.requests) == 1
    assert "Retrieved context:" in llm_provider.requests[0].prompt
    assert "Consistent sleep routines" in llm_provider.requests[0].prompt
    assert "How can sleep routines help?" in llm_provider.requests[0].prompt


@pytest.mark.asyncio
async def test_answer_synthesizer_does_not_call_llm_without_retrieved_context() -> None:
    llm_provider = CapturingLlmProvider()
    synthesizer = LangChainAnswerSynthesizer(llm_provider)

    answer = await synthesizer.synthesize(
        query="What helps stress?",
        language=LanguageCode.EN,
        retrieved_chunks=[],
    )

    assert "could not find relevant context" in answer.lower()
    assert llm_provider.requests == []
