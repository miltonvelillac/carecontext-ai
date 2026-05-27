from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import get_llm_provider, get_retrieval_tools
from app.ports.llm import LlmProvider
from app.ports.retrieval_tools import RetrievalToolsPort
from app.schemas.common import LanguageCode
from app.schemas.query import AudioQueryRequest, RagAnswerResponse, TextQueryRequest
from app.services.query_service import answer_audio_query, answer_text_query

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("/text", response_model=RagAnswerResponse)
async def query_text(
    request: TextQueryRequest,
    retrieval_tools: RetrievalToolsPort = Depends(get_retrieval_tools),
    llm_provider: LlmProvider = Depends(get_llm_provider),
) -> RagAnswerResponse:
    return await answer_text_query(request, retrieval_tools, llm_provider)


@router.post("/audio", response_model=RagAnswerResponse)
async def query_audio(
    file: UploadFile = File(...),
    language: LanguageCode = Form(default=LanguageCode.AUTO),
    top_k: int = Form(default=5, ge=1, le=20),
    include_tts: bool = Form(default=True),
    retrieval_tools: RetrievalToolsPort = Depends(get_retrieval_tools),
    llm_provider: LlmProvider = Depends(get_llm_provider),
) -> RagAnswerResponse:
    request = AudioQueryRequest(language=language, top_k=top_k, include_tts=include_tts)
    return await answer_audio_query(file.filename, request, retrieval_tools, llm_provider)
