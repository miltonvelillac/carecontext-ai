from carecontext_contracts.common import ProviderName

from app.schemas.audio import TextToSpeechResult, TranscriptionResult
from app.schemas.citations import Citation
from app.schemas.common import LanguageCode
from app.schemas.query import AudioQueryRequest, RagAnswerResponse, RetrievedContextChunk, TextQueryRequest
from app.schemas.safety import SafetyAction, SafetyAssessment, SafetyRiskLevel
from app.ports.retrieval_tools import RetrievalFilter as PortRetrievalFilter
from app.ports.retrieval_tools import RetrievalToolsPort, RetrievedChunk


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


async def answer_text_query(
    request: TextQueryRequest,
    retrieval_tools: RetrievalToolsPort,
) -> RagAnswerResponse:
    results = await retrieval_tools.hybrid_search(
        query=request.query,
        top_k=request.top_k,
        filters=_to_port_filters(request),
    )
    return RagAnswerResponse(
        answer=(
            "Mock answer: consistent sleep routines can support sleep quality and may "
            "help with stress management. This response is educational and uses a "
            "placeholder citation until retrieval and synthesis are implemented."
        ),
        citations=[_to_citation(result) for result in results],
        safety=_mock_safety(),
        retrieved_context=[_to_retrieved_context(result) for result in results],
        tts=TextToSpeechResult(audio_id="mock-tts", provider=ProviderName.MOCK, model="mock-tts")
        if request.include_tts
        else None,
        trace_id="mock-trace-text",
    )


async def answer_audio_query(
    filename: str | None,
    request: AudioQueryRequest,
    retrieval_tools: RetrievalToolsPort,
) -> RagAnswerResponse:
    results = await retrieval_tools.hybrid_search(
        query=f"Mock transcription for {filename or 'audio input'}",
        top_k=request.top_k,
        filters=_to_port_filters(request),
    )
    transcription = TranscriptionResult(
        text=f"Mock transcription for {filename or 'audio input'}",
        language=request.language if request.language != LanguageCode.AUTO else None,
        provider=ProviderName.MOCK,
        model="mock-stt",
    )
    return RagAnswerResponse(
        answer=(
            "Mock audio answer: the transcribed question was routed through the same "
            "placeholder RAG contract used by text queries."
        ),
        citations=[_to_citation(result) for result in results],
        safety=_mock_safety(),
        retrieved_context=[_to_retrieved_context(result) for result in results],
        transcription=transcription,
        tts=TextToSpeechResult(audio_id="mock-tts", provider=ProviderName.MOCK, model="mock-tts")
        if request.include_tts
        else None,
        trace_id="mock-trace-audio",
    )
