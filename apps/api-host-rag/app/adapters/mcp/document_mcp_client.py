from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from carecontext_contracts.common import MimeType, RuntimeCommand
from carecontext_contracts.document_mcp import (
    CleanedDocumentText,
    DocumentMcpArgumentName,
    DocumentMcpToolName,
    DocumentToolMetadata,
    ExtractedDocument,
)
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


class DocumentMcpClientError(RuntimeError):
    """Raised when the Document MCP server returns an error or malformed payload."""


class DocumentMcpClient:
    def __init__(
        self,
        *,
        command: str = RuntimeCommand.PYTHON,
        args: list[str] | None = None,
        cwd: str | Path | None = None,
    ) -> None:
        self.command = command
        self.args = args or [str(_default_document_server_path())]
        self.cwd = Path(cwd).resolve() if cwd is not None else None

    async def extract_text_from_pdf(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ExtractedDocument:
        payload = await self._call_tool(
            DocumentMcpToolName.EXTRACT_TEXT_FROM_PDF,
            {
                DocumentMcpArgumentName.CONTENT_BASE64: base64.b64encode(content).decode(
                    "ascii"
                ),
                DocumentMcpArgumentName.FILENAME: filename,
                DocumentMcpArgumentName.CONTENT_TYPE: content_type or MimeType.APPLICATION_PDF,
            },
        )
        return ExtractedDocument.model_validate(payload)

    async def clean_extracted_text(self, text: str) -> CleanedDocumentText:
        payload = await self._call_tool(
            DocumentMcpToolName.CLEAN_EXTRACTED_TEXT,
            {DocumentMcpArgumentName.TEXT: text},
        )
        return CleanedDocumentText.model_validate(payload)

    async def get_document_metadata(
        self,
        text: str,
        filename: str,
        user_title: str | None = None,
    ) -> DocumentToolMetadata:
        payload = await self._call_tool(
            DocumentMcpToolName.GET_DOCUMENT_METADATA,
            {
                DocumentMcpArgumentName.TEXT: text,
                DocumentMcpArgumentName.FILENAME: filename,
                DocumentMcpArgumentName.USER_TITLE: user_title,
            },
        )
        return DocumentToolMetadata.model_validate(payload)

    async def _call_tool(
        self,
        name: DocumentMcpToolName,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        server = StdioServerParameters(
            command=self.command,
            args=self.args,
            cwd=self.cwd,
        )
        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(str(name), arguments)

        if result.isError:
            raise DocumentMcpClientError(_result_text(result.content) or f"{name} failed")

        if result.structuredContent is not None:
            return result.structuredContent

        text_payload = _result_text(result.content)
        if not text_payload:
            raise DocumentMcpClientError(f"{name} returned no content")
        try:
            decoded = json.loads(text_payload)
        except json.JSONDecodeError as exc:
            raise DocumentMcpClientError(f"{name} returned invalid JSON content") from exc
        if not isinstance(decoded, dict):
            raise DocumentMcpClientError(f"{name} returned non-object JSON content")
        return decoded


def _result_text(content: list[Any]) -> str:
    return "\n".join(item.text for item in content if getattr(item, "type", None) == "text")


def _default_document_server_path() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "services" / "document-mcp-server" / "server.py"
        if candidate.exists():
            return candidate
    return Path("services") / "document-mcp-server" / "server.py"
