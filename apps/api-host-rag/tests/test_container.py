from pathlib import Path

import pytest

from app.adapters.mock.llm import MockLlmProvider
from app.adapters.mcp.retrieval_mcp_client import RetrievalMcpClient
from app.adapters.openai.llm import OpenAiLlmProvider
from app.chains.langchain_answer_synthesizer import LangChainAnswerSynthesizer
from app.chains.langchain_safety_classifier import LangChainSafetyClassifier
from app.adapters.local.document_repository import LocalJsonDocumentRepository
from app.composition.container import (
    build_answer_synthesizer,
    build_document_repository,
    build_llm_provider,
    build_retrieval_tools,
    build_safety_classifier,
)
from app.core.config import Settings
from carecontext_contracts.common import ChromaHnswSpace, ProviderName
from carecontext_contracts.retrieval_mcp import RetrievalEmbeddingsProvider


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


def test_settings_treat_optional_empty_strings_as_none() -> None:
    settings = Settings(
        openai_llm_model="",
        retrieval_min_score="",
        chroma_host="",
    )

    assert settings.openai_llm_model is None
    assert settings.retrieval_min_score is None
    assert settings.chroma_host is None


def test_build_document_repository_uses_local_json_repository(tmp_path: Path) -> None:
    repository = build_document_repository(Settings(data_dir=str(tmp_path)))

    assert isinstance(repository, LocalJsonDocumentRepository)
    assert repository.path == tmp_path / "documents.json"


def test_build_retrieval_tools_uses_retrieval_mcp_client_with_local_chroma_path(
    tmp_path: Path,
) -> None:
    settings = Settings(data_dir=str(tmp_path), chroma_host=None)

    retrieval_tools = build_retrieval_tools(settings)

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.env is not None
    assert retrieval_tools.env["CARECONTEXT_CHROMA_PATH"] == str(tmp_path / "chroma")
    assert retrieval_tools.env["CARECONTEXT_CHROMA_HNSW_SPACE"] == ChromaHnswSpace.COSINE.value
    assert retrieval_tools.env["CARECONTEXT_RETRIEVAL_CANDIDATE_MULTIPLIER"] == "5"
    assert (
        retrieval_tools.env["CARECONTEXT_EMBEDDINGS_PROVIDER"]
        == RetrievalEmbeddingsProvider.DETERMINISTIC.value
    )
    assert "CARECONTEXT_CHROMA_HOST" not in retrieval_tools.env


def test_build_retrieval_tools_uses_configured_chroma_http() -> None:
    settings = Settings(chroma_host="chroma", chroma_port=8000)

    retrieval_tools = build_retrieval_tools(settings)

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.env is not None
    assert retrieval_tools.env["CARECONTEXT_CHROMA_HOST"] == "chroma"
    assert retrieval_tools.env["CARECONTEXT_CHROMA_PORT"] == "8000"
    assert "CARECONTEXT_CHROMA_PATH" not in retrieval_tools.env


def test_build_retrieval_tools_passes_configured_chroma_hnsw_space() -> None:
    retrieval_tools = build_retrieval_tools(
        Settings(chroma_hnsw_space=ChromaHnswSpace.INNER_PRODUCT)
    )

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.env is not None
    assert retrieval_tools.env["CARECONTEXT_CHROMA_HNSW_SPACE"] == ChromaHnswSpace.INNER_PRODUCT.value


def test_build_retrieval_tools_passes_configured_min_score() -> None:
    retrieval_tools = build_retrieval_tools(Settings(retrieval_min_score=0.6))

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.min_score == 0.6


def test_build_retrieval_tools_passes_configured_candidate_multiplier() -> None:
    retrieval_tools = build_retrieval_tools(Settings(retrieval_candidate_multiplier=8))

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.env is not None
    assert retrieval_tools.env["CARECONTEXT_RETRIEVAL_CANDIDATE_MULTIPLIER"] == "8"


def test_build_retrieval_tools_passes_openai_embeddings_settings() -> None:
    retrieval_tools = build_retrieval_tools(
        Settings(
            embeddings_provider=ProviderName.OPENAI,
            openai_api_key="test-key",
            openai_embedding_model="text-embedding-test",
        )
    )

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.env is not None
    assert (
        retrieval_tools.env["CARECONTEXT_EMBEDDINGS_PROVIDER"]
        == RetrievalEmbeddingsProvider.OPENAI.value
    )
    assert retrieval_tools.env["OPENAI_API_KEY"] == "test-key"
    assert retrieval_tools.env["OPENAI_EMBEDDING_MODEL"] == "text-embedding-test"


def test_build_retrieval_tools_requires_openai_api_key_for_openai_embeddings() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        build_retrieval_tools(
            Settings(embeddings_provider=ProviderName.OPENAI, openai_api_key=None)
        )
