from typing import Any

import pytest
from carecontext_contracts.retrieval_mcp import RetrievalDocumentChunk

from app.adapters.mcp.retrieval_mcp_client import RetrievalMcpClient
from app.ports.retrieval_tools import RetrievalFilter, RetrievedChunk
from app.schemas.common import LanguageCode, SourceType
from app.schemas.documents import DocumentChunk


def _document_chunk() -> DocumentChunk:
    return DocumentChunk(
        doc_id="doc-1",
        chunk_id="doc-1-chunk-1",
        title="Sleep Basics",
        text="Consistent sleep routines can support sleep quality.",
        source_type=SourceType.CURATED,
        topic_tags=["sleep"],
        language=LanguageCode.EN,
        section="Sleep routines",
        metadata={"test": "true"},
    )


def test_document_chunk_fields_are_compatible_with_retrieval_contract() -> None:
    api_fields = set(DocumentChunk.model_fields)
    contract_fields = set(RetrievalDocumentChunk.model_fields)

    assert contract_fields <= api_fields


def test_document_chunk_can_be_converted_to_retrieval_document_chunk() -> None:
    chunk = _document_chunk()

    contract_chunk = RetrievalDocumentChunk.model_validate(chunk.model_dump(mode="json"))

    assert contract_chunk.doc_id == chunk.doc_id
    assert contract_chunk.chunk_id == chunk.chunk_id
    assert contract_chunk.source_type == chunk.source_type
    assert contract_chunk.language == chunk.language


class CapturingRetrievalMcpClient(RetrievalMcpClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[Any, dict[str, Any]]] = []

    async def _call_tool(self, name: Any, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, arguments))
        if str(name) == "upsert_chunks":
            return {
                "inserted_count": 1,
                "updated_count": 0,
                "skipped_count": 0,
                "collection_name": "test",
            }
        if str(name) == "hybrid_search":
            return {
                "results": [
                    {
                        "doc_id": "doc-1",
                        "chunk_id": "doc-1-chunk-1",
                        "title": "Sleep Basics",
                        "snippet": "Consistent sleep routines can support sleep quality.",
                        "score": 0.9,
                        "section": "Sleep routines",
                        "metadata": {"source_type": "curated"},
                    }
                ]
            }
        if str(name) == "rerank_results":
            return {
                "results": [
                    {
                        "chunk": arguments["results"][0],
                        "rerank_score": 0.95,
                        "reason": "test",
                    }
                ]
            }
        raise AssertionError(f"Unexpected tool: {name}")


@pytest.mark.asyncio
async def test_upsert_chunks_sends_json_compatible_contract_payload() -> None:
    client = CapturingRetrievalMcpClient()

    result = await client.upsert_chunks([_document_chunk()])

    assert result.inserted_count == 1
    _, arguments = client.calls[0]
    payload = arguments["chunks"][0]
    assert payload["doc_id"] == "doc-1"
    assert payload["source_type"] == "curated"
    assert payload["language"] == "en"


@pytest.mark.asyncio
async def test_hybrid_search_sends_json_compatible_filters() -> None:
    client = CapturingRetrievalMcpClient()

    results = await client.hybrid_search(
        "sleep routines",
        3,
        RetrievalFilter(source_types=[SourceType.CURATED], topic_tags=["sleep"], language=LanguageCode.EN),
    )

    assert results[0].chunk_id == "doc-1-chunk-1"
    _, arguments = client.calls[0]
    assert arguments["filters"] == {
        "source_types": ["curated"],
        "topic_tags": ["sleep"],
        "language": "en",
    }


@pytest.mark.asyncio
async def test_rerank_results_sends_json_compatible_results() -> None:
    client = CapturingRetrievalMcpClient()
    result = RetrievedChunk(
        doc_id="doc-1",
        chunk_id="doc-1-chunk-1",
        title="Sleep Basics",
        snippet="Consistent sleep routines can support sleep quality.",
        score=0.9,
    )

    reranked = await client.rerank_results("sleep", [result], 1)

    assert reranked[0].rerank_score == 0.95
    _, arguments = client.calls[0]
    assert arguments["results"][0]["chunk_id"] == "doc-1-chunk-1"
