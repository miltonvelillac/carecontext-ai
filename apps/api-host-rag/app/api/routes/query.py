from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_answer_synthesizer, get_retrieval_tools, get_safety_classifier
from app.ports.retrieval_tools import RetrievalToolsPort
from app.ports.safety import SafetyClassifierPort
from app.ports.synthesis import AnswerSynthesizerPort
from app.schemas.common import LanguageCode
from app.schemas.query import AudioQueryRequest, RagAnswerResponse, TextQueryRequest
from app.services.query_service import answer_audio_query, answer_text_query

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("/text", response_model=RagAnswerResponse)
async def query_text(
    request: TextQueryRequest,
    retrieval_tools: RetrievalToolsPort = Depends(get_retrieval_tools),
    safety_classifier: SafetyClassifierPort = Depends(get_safety_classifier),
    answer_synthesizer: AnswerSynthesizerPort = Depends(get_answer_synthesizer),
) -> RagAnswerResponse:
    return await answer_text_query(request, retrieval_tools, safety_classifier, answer_synthesizer)


@router.post("/audio", response_model=RagAnswerResponse)
async def query_audio(
    file: UploadFile = File(...),
    language: LanguageCode = Form(default=LanguageCode.AUTO),
    top_k: int = Form(default=5, ge=1, le=20),
    include_tts: bool = Form(default=True),
    retrieval_tools: RetrievalToolsPort = Depends(get_retrieval_tools),
    safety_classifier: SafetyClassifierPort = Depends(get_safety_classifier),
    answer_synthesizer: AnswerSynthesizerPort = Depends(get_answer_synthesizer),
) -> RagAnswerResponse:
    request = AudioQueryRequest(language=language, top_k=top_k, include_tts=include_tts)
    return await answer_audio_query(
        file.filename,
        request,
        retrieval_tools,
        safety_classifier,
        answer_synthesizer,
    )
