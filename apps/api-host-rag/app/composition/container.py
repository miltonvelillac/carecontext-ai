"""Application composition root.

This module will build concrete adapters from settings and inject them into
services. Keep provider and MCP selection here instead of branching inside
routes or use-case services.
"""

from app.adapters.mock.document_repository import MockDocumentRepository
from app.adapters.mock.document_tools import MockDocumentTools
from app.adapters.mock.retrieval_tools import MockRetrievalTools
from app.core.config import Settings
from app.ports.document_repository import DocumentRepositoryPort
from app.ports.document_tools import DocumentToolsPort
from app.ports.retrieval_tools import RetrievalToolsPort


class AppContainer:
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
    del settings
    return MockDocumentTools()


def build_retrieval_tools(settings: Settings) -> RetrievalToolsPort:
    del settings
    return MockRetrievalTools()


def build_document_repository(settings: Settings) -> DocumentRepositoryPort:
    del settings
    return MockDocumentRepository()
