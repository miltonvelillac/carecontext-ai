"""Application composition root.

This module will build concrete adapters from settings and inject them into
services. Keep provider and MCP selection here instead of branching inside
routes or use-case services.
"""

import shlex
import os
from pathlib import Path

from carecontext_contracts.common import McpTransport
from app.adapters.mock.document_repository import MockDocumentRepository
from app.adapters.mcp.document_mcp_client import DocumentMcpClient
from app.adapters.mcp.retrieval_mcp_client import RetrievalMcpClient
from app.core.config import Settings
from app.ports.document_repository import DocumentRepositoryPort
from app.ports.document_tools import DocumentToolsPort
from app.ports.retrieval_tools import RetrievalToolsPort


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
        self._document_tools: DocumentToolsPort | None = None
        self._retrieval_tools: RetrievalToolsPort | None = None
        self._document_repository: DocumentRepositoryPort | None = None

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
    )


def build_document_repository(settings: Settings) -> DocumentRepositoryPort:
    """Factory function for the document repository implementation."""

    del settings
    return MockDocumentRepository()


def _build_retrieval_mcp_env(settings: Settings) -> dict[str, str]:
    env = os.environ.copy()
    if settings.chroma_host:
        env["CARECONTEXT_CHROMA_HOST"] = settings.chroma_host
        env["CARECONTEXT_CHROMA_PORT"] = str(settings.chroma_port)
        env.pop("CARECONTEXT_CHROMA_PATH", None)
    else:
        env["CARECONTEXT_CHROMA_PATH"] = str(Path(settings.data_dir) / "chroma")
        env.pop("CARECONTEXT_CHROMA_HOST", None)
        env.pop("CARECONTEXT_CHROMA_PORT", None)
    return env
