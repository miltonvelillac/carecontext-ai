from fastapi import APIRouter, File, Form, UploadFile

from app.schemas.common import LanguageCode
from app.schemas.query import AudioQueryRequest, RagAnswerResponse, TextQueryRequest
from app.services.query_service import answer_audio_query, answer_text_query

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("/text", response_model=RagAnswerResponse)
async def query_text(request: TextQueryRequest) -> RagAnswerResponse:
    return await answer_text_query(request)


@router.post("/audio", response_model=RagAnswerResponse)
async def query_audio(
    file: UploadFile = File(...),
    language: LanguageCode = Form(default=LanguageCode.AUTO),
    top_k: int = Form(default=5, ge=1, le=20),
    include_tts: bool = Form(default=True),
) -> RagAnswerResponse:
    request = AudioQueryRequest(language=language, top_k=top_k, include_tts=include_tts)
    return await answer_audio_query(file.filename, request)
