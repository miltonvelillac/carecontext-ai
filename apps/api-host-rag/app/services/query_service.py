"""Query use cases.

Service Layer: API routes delegate query workflows here so orchestration can
depend on ports and DTOs instead of FastAPI request objects.
"""

from carecontext_contracts.common import ProviderName

from app.schemas.audio import TextToSpeechResult, TranscriptionResult
from app.schemas.citations import Citation
from app.schemas.common import LanguageCode
from app.schemas.query import AudioQueryRequest, RagAnswerResponse, RetrievedContextChunk, TextQueryRequest
from app.schemas.safety import SafetyAction
from app.ports.retrieval_tools import RetrievalFilter as PortRetrievalFilter
from app.ports.retrieval_tools import RetrievalToolsPort, RetrievedChunk
from app.ports.safety import SafetyClassifierPort
from app.ports.synthesis import AnswerSynthesizerPort
from app.services.safety_service import (
    apply_safety_caveat,
    crisis_response,
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
    safety_classifier: SafetyClassifierPort,
    answer_synthesizer: AnswerSynthesizerPort,
) -> RagAnswerResponse:
    safety = await safety_classifier.classify(request.query)
    if safety.action == SafetyAction.REDIRECT:
        return RagAnswerResponse(
            answer=crisis_response(safety),
            citations=[],
            safety=safety,
            retrieved_context=[],
            tts=TextToSpeechResult(audio_id="mock-tts", provider=ProviderName.MOCK, model="mock-tts")
            if request.include_tts
            else None,
            trace_id="mock-trace-text",
        )

    retrieved_chunks = await retrieval_tools.retrieve_chunks(
        query=request.query,
        top_k=request.top_k,
        filters=_to_port_filters(request),
    )
    return RagAnswerResponse(
        answer=apply_safety_caveat(
            await answer_synthesizer.synthesize(
                query=request.query,
                language=request.language,
                retrieved_chunks=retrieved_chunks,
            ),
            safety,
        ),
        citations=[_to_citation(chunk) for chunk in retrieved_chunks],
        safety=safety,
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
    safety_classifier: SafetyClassifierPort,
    answer_synthesizer: AnswerSynthesizerPort,
) -> RagAnswerResponse:
    transcribed_query = f"Mock transcription for {filename or 'audio input'}"
    safety = await safety_classifier.classify(transcribed_query)
    if safety.action == SafetyAction.REDIRECT:
        transcription = TranscriptionResult(
            text=transcribed_query,
            language=request.language if request.language != LanguageCode.AUTO else None,
            provider=ProviderName.MOCK,
            model="mock-stt",
        )
        return RagAnswerResponse(
            answer=crisis_response(safety),
            citations=[],
            safety=safety,
            retrieved_context=[],
            transcription=transcription,
            tts=TextToSpeechResult(audio_id="mock-tts", provider=ProviderName.MOCK, model="mock-tts")
            if request.include_tts
            else None,
            trace_id="mock-trace-audio",
        )

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
        answer=apply_safety_caveat(
            await answer_synthesizer.synthesize(
                query=transcribed_query,
                language=request.language,
                retrieved_chunks=retrieved_chunks,
            ),
            safety,
        ),
        citations=[_to_citation(chunk) for chunk in retrieved_chunks],
        safety=safety,
        retrieved_context=[_to_retrieved_context(chunk) for chunk in retrieved_chunks],
        transcription=transcription,
        tts=TextToSpeechResult(audio_id="mock-tts", provider=ProviderName.MOCK, model="mock-tts")
        if request.include_tts
        else None,
        trace_id="mock-trace-audio",
    )
