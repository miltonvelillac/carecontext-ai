from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from carecontext_contracts.common import RuntimeCommand
from carecontext_contracts.retrieval_mcp import (
    ChunkDocumentRequest,
    ChunkDocumentResult,
    HybridSearchResult,
    RerankResultsResult,
    RetrievalDocumentChunk,
    RetrievalFilter as ContractRetrievalFilter,
    RetrievalMcpArgumentName,
    RetrievalMcpToolName,
    RetrievedChunk as ContractRetrievedChunk,
)
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.ports.retrieval_tools import (
    RerankedChunk,
    RetrievalFilter,
    RetrievedChunk,
    UpsertChunksResult,
)
from app.schemas.common import LanguageCode, SourceType
from app.schemas.documents import DocumentChunk


class RetrievalMcpClientError(RuntimeError):
    """Raised when the Retrieval MCP server returns an error or malformed payload."""


class RetrievalMcpClient:
    """Adapter that implements retrieval tooling through a Retrieval MCP server."""

    def __init__(
        self,
        *,
        command: str = RuntimeCommand.PYTHON,
        args: list[str] | None = None,
        cwd: str | Path | None = None,
        env: dict[str, str] | None = None,
        min_score: float | None = None,
    ) -> None:
        self.command = command
        self.args = args or [str(_default_retrieval_server_path())]
        self.cwd = Path(cwd).resolve() if cwd is not None else None
        self.env = env
        self.min_score = min_score

    async def chunk_document(
        self,
        *,
        doc_id: str,
        title: str,
        text: str,
        source_type: SourceType,
        topic_tags: list[str],
        language: LanguageCode,
        section: str | None = None,
        quality_score: float | None = None,
        metadata: dict[str, str] | None = None,
    ) -> list[DocumentChunk]:
        request = ChunkDocumentRequest(
            doc_id=doc_id,
            title=title,
            text=text,
            source_type=source_type,
            topic_tags=topic_tags,
            language=language,
            section=section,
            quality_score=quality_score,
            metadata=metadata or {},
        )
        payload = await self._call_tool(
            RetrievalMcpToolName.CHUNK_DOCUMENT,
            {RetrievalMcpArgumentName.REQUEST: request.model_dump(mode="json")},
        )
        result = ChunkDocumentResult.model_validate(payload)
        return [
            DocumentChunk.model_validate(chunk.model_dump(mode="json"))
            for chunk in result.chunks
        ]

    async def upsert_chunks(self, chunks: list[DocumentChunk]) -> UpsertChunksResult:
        contract_chunks = [
            RetrievalDocumentChunk.model_validate(chunk.model_dump(mode="json"))
            for chunk in chunks
        ]
        payload = await self._call_tool(
            RetrievalMcpToolName.UPSERT_CHUNKS,
            {
                RetrievalMcpArgumentName.CHUNKS: [
                    chunk.model_dump(mode="json") for chunk in contract_chunks
                ],
            },
        )
        return UpsertChunksResult.model_validate(payload)

    async def retrieve_chunks(
        self,
        query: str,
        top_k: int,
        filters: RetrievalFilter | None = None,
    ) -> list[RetrievedChunk]:
        arguments: dict[str, Any] = {
            RetrievalMcpArgumentName.QUERY: query,
            RetrievalMcpArgumentName.TOP_K: top_k,
        }
        if filters is not None:
            contract_filters = ContractRetrievalFilter.model_validate(
                filters.model_dump(mode="json")
            )
            if contract_filters.min_score is None:
                contract_filters.min_score = self.min_score
            arguments[RetrievalMcpArgumentName.FILTERS] = contract_filters.model_dump(
                mode="json",
                exclude_none=True,
            )
        elif self.min_score is not None:
            arguments[RetrievalMcpArgumentName.FILTERS] = ContractRetrievalFilter(
                min_score=self.min_score
            ).model_dump(mode="json", exclude_none=True)

        payload = await self._call_tool(RetrievalMcpToolName.HYBRID_SEARCH, arguments)
        search_result = HybridSearchResult.model_validate(payload)
        return [
            RetrievedChunk.model_validate(chunk.model_dump())
            for chunk in search_result.results
        ]

    async def rerank_results(
        self,
        query: str,
        retrieved_chunks: list[RetrievedChunk],
        top_k: int,
    ) -> list[RerankedChunk]:
        contract_results = [
            ContractRetrievedChunk.model_validate(chunk.model_dump(mode="json"))
            for chunk in retrieved_chunks
        ]
        payload = await self._call_tool(
            RetrievalMcpToolName.RERANK_RESULTS,
            {
                RetrievalMcpArgumentName.QUERY: query,
                RetrievalMcpArgumentName.RESULTS: [
                    chunk.model_dump(mode="json") for chunk in contract_results
                ],
                RetrievalMcpArgumentName.TOP_K: top_k,
            },
        )
        rerank_result = RerankResultsResult.model_validate(payload)
        return [RerankedChunk.model_validate(chunk.model_dump()) for chunk in rerank_result.results]

    async def _call_tool(
        self,
        name: RetrievalMcpToolName,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        server = StdioServerParameters(
            command=self.command,
            args=self.args,
            cwd=self.cwd,
            env=self.env,
        )
        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(str(name), arguments)

        if result.isError:
            raise RetrievalMcpClientError(_result_text(result.content) or f"{name} failed")

        if result.structuredContent is not None:
            return result.structuredContent

        text_payload = _result_text(result.content)
        if not text_payload:
            raise RetrievalMcpClientError(f"{name} returned no content")
        try:
            decoded = json.loads(text_payload)
        except json.JSONDecodeError as exc:
            raise RetrievalMcpClientError(f"{name} returned invalid JSON content") from exc
        if not isinstance(decoded, dict):
            raise RetrievalMcpClientError(f"{name} returned non-object JSON content")
        return decoded


def _result_text(content: list[Any]) -> str:
    return "\n".join(item.text for item in content if getattr(item, "type", None) == "text")


def _default_retrieval_server_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "services" / "retrieval-mcp-server" / "server.py"
        if candidate.exists():
            return candidate
    return Path("services") / "retrieval-mcp-server" / "server.py"
