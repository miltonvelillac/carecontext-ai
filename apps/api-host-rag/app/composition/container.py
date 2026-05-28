"""Application composition root.

This module will build concrete adapters from settings and inject them into
services. Keep provider and MCP selection here instead of branching inside
routes or use-case services.
"""

import shlex
import os
from pathlib import Path

from carecontext_contracts.common import McpTransport, ProviderName
from carecontext_contracts.retrieval_mcp import RetrievalEmbeddingsProvider
from app.chains.langchain_answer_synthesizer import LangChainAnswerSynthesizer
from app.chains.langchain_safety_classifier import LangChainSafetyClassifier
from app.adapters.mock.document_repository import MockDocumentRepository
from app.adapters.mock.llm import MockLlmProvider
from app.adapters.mcp.document_mcp_client import DocumentMcpClient
from app.adapters.mcp.retrieval_mcp_client import RetrievalMcpClient
from app.adapters.openai.llm import OpenAiLlmProvider
from app.core.config import Settings
from app.ports.document_repository import DocumentRepositoryPort
from app.ports.document_tools import DocumentToolsPort
from app.ports.llm import LlmProvider
from app.ports.retrieval_tools import RetrievalToolsPort
from app.ports.safety import SafetyClassifierPort
from app.ports.synthesis import AnswerSynthesizerPort


class AppContainer:
    """Composition root for application dependencies.

    This class is where dependency injection is wired: app code asks for ports
    such as `DocumentToolsPort`, and the container decides which concrete
    adapter implements that port, such as `DocumentMcpClient`.

    Patterns applied here:
    - Dependency Injection: routers/services receive dependencies instead of
      constructing adapters directly.
    - Ports and Adapters: the app depends on port interfaces while this layer
      selects concrete adapters.
    - Lazy Singleton per app instance: each dependency is built once on first
      access and then reused for the FastAPI application lifetime.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._llm_provider: LlmProvider | None = None
        self._answer_synthesizer: AnswerSynthesizerPort | None = None
        self._document_tools: DocumentToolsPort | None = None
        self._retrieval_tools: RetrievalToolsPort | None = None
        self._document_repository: DocumentRepositoryPort | None = None
        self._safety_classifier: SafetyClassifierPort | None = None

    @property
    def llm_provider(self) -> LlmProvider:
        if self._llm_provider is None:
            self._llm_provider = build_llm_provider(self.settings)
        return self._llm_provider

    @property
    def answer_synthesizer(self) -> AnswerSynthesizerPort:
        if self._answer_synthesizer is None:
            self._answer_synthesizer = build_answer_synthesizer(self.llm_provider)
        return self._answer_synthesizer

    @property
    def document_tools(self) -> DocumentToolsPort:
        if self._document_tools is None:
            self._document_tools = build_document_tools(self.settings)
        return self._document_tools

    @property
    def retrieval_tools(self) -> RetrievalToolsPort:
        if self._retrieval_tools is None:
            self._retrieval_tools = build_retrieval_tools(self.settings)
        return self._retrieval_tools

    @property
    def document_repository(self) -> DocumentRepositoryPort:
        if self._document_repository is None:
            self._document_repository = build_document_repository(self.settings)
        return self._document_repository

    @property
    def safety_classifier(self) -> SafetyClassifierPort:
        if self._safety_classifier is None:
            self._safety_classifier = build_safety_classifier(self.llm_provider)
        return self._safety_classifier


def build_llm_provider(settings: Settings) -> LlmProvider:
    """Factory function for answer synthesis providers."""

    if settings.llm_provider == ProviderName.MOCK:
        return MockLlmProvider()
    if settings.llm_provider == ProviderName.OPENAI:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        return OpenAiLlmProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_llm_model,
        )
    raise ValueError(f"Unsupported LLM provider '{settings.llm_provider}'.")


def build_answer_synthesizer(llm_provider: LlmProvider) -> AnswerSynthesizerPort:
    """Factory function for answer synthesis workflows."""

    return LangChainAnswerSynthesizer(llm_provider)


def build_safety_classifier(llm_provider: LlmProvider) -> SafetyClassifierPort:
    """Factory function for safety classification workflows."""

    return LangChainSafetyClassifier(llm_provider)


def build_document_tools(settings: Settings) -> DocumentToolsPort:
    """Factory function that selects the concrete document tools adapter."""

    if settings.document_mcp_transport != McpTransport.STDIO:
        raise ValueError(
            "Unsupported Document MCP transport "
            f"'{settings.document_mcp_transport}'. Supported: {McpTransport.STDIO}"
        )
    return DocumentMcpClient(
        command=settings.document_mcp_command,
        args=shlex.split(settings.document_mcp_args) if settings.document_mcp_args else None,
        cwd=settings.document_mcp_cwd,
    )


def build_retrieval_tools(settings: Settings) -> RetrievalToolsPort:
    """Factory function for the retrieval tools strategy."""

    if settings.retrieval_mcp_transport != McpTransport.STDIO:
        raise ValueError(
            "Unsupported Retrieval MCP transport "
            f"'{settings.retrieval_mcp_transport}'. Supported: {McpTransport.STDIO}"
        )
    return RetrievalMcpClient(
        command=settings.retrieval_mcp_command,
        args=shlex.split(settings.retrieval_mcp_args) if settings.retrieval_mcp_args else None,
        cwd=settings.retrieval_mcp_cwd,
        env=_build_retrieval_mcp_env(settings),
        min_score=settings.retrieval_min_score,
    )


def build_document_repository(settings: Settings) -> DocumentRepositoryPort:
    """Factory function for the document repository implementation."""

    del settings
    return MockDocumentRepository()


def _build_retrieval_mcp_env(settings: Settings) -> dict[str, str]:
    env = os.environ.copy()
    env["CARECONTEXT_EMBEDDINGS_PROVIDER"] = _retrieval_embeddings_provider(settings)
    env["CARECONTEXT_CHROMA_HNSW_SPACE"] = settings.chroma_hnsw_space.value
    env["CARECONTEXT_RETRIEVAL_CANDIDATE_MULTIPLIER"] = str(
        settings.retrieval_candidate_multiplier
    )
    if settings.openai_embedding_model:
        env["OPENAI_EMBEDDING_MODEL"] = settings.openai_embedding_model
    if settings.openai_api_key:
        env["OPENAI_API_KEY"] = settings.openai_api_key

    if settings.chroma_host:
        env["CARECONTEXT_CHROMA_HOST"] = settings.chroma_host
        env["CARECONTEXT_CHROMA_PORT"] = str(settings.chroma_port)
        env.pop("CARECONTEXT_CHROMA_PATH", None)
    else:
        env["CARECONTEXT_CHROMA_PATH"] = str(Path(settings.data_dir) / "chroma")
        env.pop("CARECONTEXT_CHROMA_HOST", None)
        env.pop("CARECONTEXT_CHROMA_PORT", None)
    return env


def _retrieval_embeddings_provider(settings: Settings) -> str:
    if settings.embeddings_provider == ProviderName.MOCK:
        return RetrievalEmbeddingsProvider.DETERMINISTIC.value
    if settings.embeddings_provider == ProviderName.OPENAI:
        if not settings.openai_api_key:
            raise ValueError(
                f"OPENAI_API_KEY is required when EMBEDDINGS_PROVIDER={ProviderName.OPENAI.value}."
            )
        return RetrievalEmbeddingsProvider.OPENAI.value
    raise ValueError(f"Unsupported embeddings provider '{settings.embeddings_provider}'.")
