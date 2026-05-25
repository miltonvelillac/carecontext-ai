from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.audio import TextToSpeechResult, TranscriptionResult
from app.schemas.common import LanguageCode
from app.schemas.query import AudioQueryRequest, RagAnswerResponse, TextQueryRequest
from app.schemas.safety import SafetyAction, SafetyAssessment, SafetyRiskLevel

router = APIRouter(prefix="/api/query", tags=["query"])


def _mock_safety() -> SafetyAssessment:
    return SafetyAssessment(
        risk_level=SafetyRiskLevel.LOW,
        action=SafetyAction.ALLOW,
        disclaimer="Educational information only. Not medical advice.",
    )


@router.post("/text", response_model=RagAnswerResponse)
async def query_text(request: TextQueryRequest) -> RagAnswerResponse:
    return RagAnswerResponse(
        answer=(
            "This is a typed placeholder response. Retrieval, synthesis, citations, "
            "and provider calls are not implemented yet."
        ),
        citations=[],
        safety=_mock_safety(),
        retrieved_context=[],
        tts=TextToSpeechResult(audio_id="mock-tts") if request.include_tts else None,
    )


@router.post("/audio", response_model=RagAnswerResponse)
async def query_audio(
    file: UploadFile = File(...),
    language: LanguageCode = Form(default=LanguageCode.AUTO),
    top_k: int = Form(default=5, ge=1, le=20),
    include_tts: bool = Form(default=True),
) -> RagAnswerResponse:
    request = AudioQueryRequest(language=language, top_k=top_k, include_tts=include_tts)
    transcription = TranscriptionResult(
        text=f"Mock transcription for {file.filename or 'audio input'}",
        language=request.language if request.language != LanguageCode.AUTO else None,
        provider="mock",
        model="mock-stt",
    )
    return RagAnswerResponse(
        answer=(
            "This is a typed placeholder audio response. STT, RAG, citations, and TTS "
            "are not implemented yet."
        ),
        citations=[],
        safety=_mock_safety(),
        retrieved_context=[],
        transcription=transcription,
        tts=TextToSpeechResult(audio_id="mock-tts", provider="mock", model="mock-tts")
        if request.include_tts
        else None,
    )
