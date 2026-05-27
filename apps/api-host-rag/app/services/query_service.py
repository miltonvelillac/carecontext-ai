"""Query use cases.

Service Layer: API routes delegate query workflows here so orchestration can
depend on ports and DTOs instead of FastAPI request objects.
"""

from carecontext_contracts.common import ProviderName
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.audio import TextToSpeechResult, TranscriptionResult
from app.schemas.citations import Citation
from app.schemas.common import LanguageCode
from app.schemas.query import AudioQueryRequest, RagAnswerResponse, RetrievedContextChunk, TextQueryRequest
from app.schemas.safety import SafetyAction, SafetyAssessment, SafetyRiskLevel
from app.ports.llm import LlmProvider, LlmRequest
from app.ports.retrieval_tools import RetrievalFilter as PortRetrievalFilter
from app.ports.retrieval_tools import RetrievalToolsPort, RetrievedChunk

RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a bilingual educational health and psychology RAG assistant. "
            "You must stay grounded in the provided context and avoid unsupported "
            "medical claims.",
        ),
        (
            "human",
            "Answer the question using only the retrieved context. "
            "If the context is empty or insufficient, say that relevant context was "
            "not found. Keep the answer educational, avoid diagnosis or treatment "
            "instructions, and mention that it is not medical advice.\n\n"
            "Language: {language}\n\n"
            "Retrieved context:\n{context}\n\n"
            "Question: {query}",
        ),
    ]
)


def _mock_safety() -> SafetyAssessment:
    return SafetyAssessment(
        risk_level=SafetyRiskLevel.LOW,
        action=SafetyAction.ALLOW,
        disclaimer="Educational information only. Not medical advice.",
    )


def _to_port_filters(request: TextQueryRequest | AudioQueryRequest) -> PortRetrievalFilter | None:
    if request.filters is None:
        return None
    return PortRetrievalFilter(
        source_types=request.filters.source_types,
        topic_tags=request.filters.topic_tags,
        language=request.filters.language,
    )


def _to_citation(chunk: RetrievedChunk) -> Citation:
    return Citation(
        doc_id=chunk.doc_id,
        title=chunk.title,
        chunk_id=chunk.chunk_id,
        snippet=chunk.snippet,
        section=chunk.section,
        score=chunk.score,
        metadata=chunk.metadata,
    )


def _to_retrieved_context(chunk: RetrievedChunk) -> RetrievedContextChunk:
    return RetrievedContextChunk(
        doc_id=chunk.doc_id,
        title=chunk.title,
        chunk_id=chunk.chunk_id,
        snippet=chunk.snippet,
        score=chunk.score,
        section=chunk.section,
        metadata=chunk.metadata,
    )


def _build_rag_prompt(
    query: str,
    retrieved_chunks: list[RetrievedChunk],
    language: LanguageCode,
) -> str:
    context = "\n".join(
        f"[{index}] {chunk.title} ({chunk.chunk_id}): {chunk.snippet}"
        for index, chunk in enumerate(retrieved_chunks, start=1)
    )
    messages = RAG_PROMPT_TEMPLATE.format_messages(
        language=str(language),
        context=context,
        query=query,
    )
    return "\n\n".join(message.content for message in messages)


def _rag_system_prompt() -> str:
    system_message = RAG_PROMPT_TEMPLATE.messages[0].format()
    return str(system_message.content)


async def _compose_grounded_answer(
    *,
    query: str,
    language: LanguageCode,
    retrieved_chunks: list[RetrievedChunk],
    llm_provider: LlmProvider,
) -> str:
    if not retrieved_chunks:
        return (
            "I could not find relevant context in the indexed documents for this question. "
            "This assistant is educational and not a substitute for professional care."
        )

    response = await llm_provider.generate(
        LlmRequest(
            prompt=_build_rag_prompt(query, retrieved_chunks, language),
            system_prompt=_rag_system_prompt(),
            language=str(language),
        )
    )
    return response.text


async def answer_text_query(
    request: TextQueryRequest,
    retrieval_tools: RetrievalToolsPort,
    llm_provider: LlmProvider,
) -> RagAnswerResponse:
    retrieved_chunks = await retrieval_tools.retrieve_chunks(
        query=request.query,
        top_k=request.top_k,
        filters=_to_port_filters(request),
    )
    return RagAnswerResponse(
        answer=await _compose_grounded_answer(
            query=request.query,
            language=request.language,
            retrieved_chunks=retrieved_chunks,
            llm_provider=llm_provider,
        ),
        citations=[_to_citation(chunk) for chunk in retrieved_chunks],
        safety=_mock_safety(),
        retrieved_context=[_to_retrieved_context(chunk) for chunk in retrieved_chunks],
        tts=TextToSpeechResult(audio_id="mock-tts", provider=ProviderName.MOCK, model="mock-tts")
        if request.include_tts
        else None,
        trace_id="mock-trace-text",
    )


async def answer_audio_query(
    filename: str | None,
    request: AudioQueryRequest,
    retrieval_tools: RetrievalToolsPort,
    llm_provider: LlmProvider,
) -> RagAnswerResponse:
    transcribed_query = f"Mock transcription for {filename or 'audio input'}"
    retrieved_chunks = await retrieval_tools.retrieve_chunks(
        query=transcribed_query,
        top_k=request.top_k,
        filters=_to_port_filters(request),
    )
    transcription = TranscriptionResult(
        text=transcribed_query,
        language=request.language if request.language != LanguageCode.AUTO else None,
        provider=ProviderName.MOCK,
        model="mock-stt",
    )
    return RagAnswerResponse(
        answer=await _compose_grounded_answer(
            query=transcribed_query,
            language=request.language,
            retrieved_chunks=retrieved_chunks,
            llm_provider=llm_provider,
        ),
        citations=[_to_citation(chunk) for chunk in retrieved_chunks],
        safety=_mock_safety(),
        retrieved_context=[_to_retrieved_context(chunk) for chunk in retrieved_chunks],
        transcription=transcription,
        tts=TextToSpeechResult(audio_id="mock-tts", provider=ProviderName.MOCK, model="mock-tts")
        if request.include_tts
        else None,
        trace_id="mock-trace-audio",
    )
