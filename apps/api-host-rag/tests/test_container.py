from pathlib import Path

import pytest

from app.adapters.mock.llm import MockLlmProvider
from app.adapters.mcp.retrieval_mcp_client import RetrievalMcpClient
from app.adapters.openai.llm import OpenAiLlmProvider
from app.chains.langchain_answer_synthesizer import LangChainAnswerSynthesizer
from app.chains.langchain_safety_classifier import LangChainSafetyClassifier
from app.composition.container import (
    build_answer_synthesizer,
    build_llm_provider,
    build_retrieval_tools,
    build_safety_classifier,
)
from app.core.config import Settings
from carecontext_contracts.common import ProviderName


def test_build_llm_provider_uses_mock_provider_by_default() -> None:
    llm_provider = build_llm_provider(Settings())

    assert isinstance(llm_provider, MockLlmProvider)


def test_build_llm_provider_uses_openai_provider_when_configured() -> None:
    llm_provider = build_llm_provider(
        Settings(
            llm_provider=ProviderName.OPENAI,
            openai_api_key="test-key",
            openai_llm_model="gpt-test",
        )
    )

    assert isinstance(llm_provider, OpenAiLlmProvider)
    assert llm_provider.model == "gpt-test"


def test_build_llm_provider_requires_openai_api_key_when_configured() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        build_llm_provider(Settings(llm_provider=ProviderName.OPENAI, openai_api_key=None))


def test_build_answer_synthesizer_uses_langchain_workflow() -> None:
    answer_synthesizer = build_answer_synthesizer(MockLlmProvider())

    assert isinstance(answer_synthesizer, LangChainAnswerSynthesizer)


def test_build_safety_classifier_uses_langchain_workflow() -> None:
    safety_classifier = build_safety_classifier(MockLlmProvider())

    assert isinstance(safety_classifier, LangChainSafetyClassifier)


def test_build_retrieval_tools_uses_retrieval_mcp_client_with_local_chroma_path(
    tmp_path: Path,
) -> None:
    settings = Settings(data_dir=str(tmp_path), chroma_host=None)

    retrieval_tools = build_retrieval_tools(settings)

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.env is not None
    assert retrieval_tools.env["CARECONTEXT_CHROMA_PATH"] == str(tmp_path / "chroma")
    assert "CARECONTEXT_CHROMA_HOST" not in retrieval_tools.env


def test_build_retrieval_tools_uses_configured_chroma_http() -> None:
    settings = Settings(chroma_host="chroma", chroma_port=8000)

    retrieval_tools = build_retrieval_tools(settings)

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.env is not None
    assert retrieval_tools.env["CARECONTEXT_CHROMA_HOST"] == "chroma"
    assert retrieval_tools.env["CARECONTEXT_CHROMA_PORT"] == "8000"
    assert "CARECONTEXT_CHROMA_PATH" not in retrieval_tools.env
