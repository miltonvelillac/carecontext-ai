from app.schemas.audio import TextToSpeechResult, TranscriptionResult
from app.schemas.common import LanguageCode
from app.schemas.query import AudioQueryRequest, RagAnswerResponse, TextQueryRequest
from app.schemas.safety import SafetyAction, SafetyAssessment, SafetyRiskLevel
from app.services.mock_corpus import mock_citation, mock_retrieved_context


def mock_safety() -> SafetyAssessment:
    return SafetyAssessment(
        risk_level=SafetyRiskLevel.LOW,
        action=SafetyAction.ALLOW,
        disclaimer="Educational information only. Not medical advice.",
    )


async def answer_text_query(request: TextQueryRequest) -> RagAnswerResponse:
    return RagAnswerResponse(
        answer=(
            "Mock answer: consistent sleep routines can support sleep quality and may "
            "help with stress management. This response is educational and uses a "
            "placeholder citation until retrieval and synthesis are implemented."
        ),
        citations=[mock_citation()],
        safety=mock_safety(),
        retrieved_context=[mock_retrieved_context()],
        tts=TextToSpeechResult(audio_id="mock-tts", provider="mock", model="mock-tts")
        if request.include_tts
        else None,
        trace_id="mock-trace-text",
    )


async def answer_audio_query(filename: str | None, request: AudioQueryRequest) -> RagAnswerResponse:
    transcription = TranscriptionResult(
        text=f"Mock transcription for {filename or 'audio input'}",
        language=request.language if request.language != LanguageCode.AUTO else None,
        provider="mock",
        model="mock-stt",
    )
    return RagAnswerResponse(
        answer=(
            "Mock audio answer: the transcribed question was routed through the same "
            "placeholder RAG contract used by text queries."
        ),
        citations=[mock_citation()],
        safety=mock_safety(),
        retrieved_context=[mock_retrieved_context()],
        transcription=transcription,
        tts=TextToSpeechResult(audio_id="mock-tts", provider="mock", model="mock-tts")
        if request.include_tts
        else None,
        trace_id="mock-trace-audio",
    )

