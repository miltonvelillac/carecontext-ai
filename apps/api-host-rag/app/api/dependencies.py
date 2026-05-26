from typing import Annotated

from fastapi import Depends, Request

from app.composition.container import AppContainer
from app.ports.document_repository import DocumentRepositoryPort
from app.ports.document_tools import DocumentToolsPort
from app.ports.retrieval_tools import RetrievalToolsPort


def get_container(request: Request) -> AppContainer:
    """Return the app-level composition root stored on FastAPI state."""

    return request.app.state.container


def get_document_tools(
    container: Annotated[AppContainer, Depends(get_container)],
) -> DocumentToolsPort:
    """FastAPI dependency injection bridge for the document tools port."""

    return container.document_tools


def get_retrieval_tools(
    container: Annotated[AppContainer, Depends(get_container)],
) -> RetrievalToolsPort:
    """FastAPI dependency injection bridge for the retrieval tools port."""

    return container.retrieval_tools


def get_document_repository(
    container: Annotated[AppContainer, Depends(get_container)],
) -> DocumentRepositoryPort:
    """FastAPI dependency injection bridge for the document repository port."""

    return container.document_repository
