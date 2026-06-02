from carecontext_contracts.common import McpTransport
from carecontext_contracts.retrieval_mcp import (
    ChunkDocumentRequest,
    ChunkDocumentResult,
    HybridSearchResult,
    RerankResultsResult,
    RetrievalDocumentChunk,
    RetrievalFilter,
    RetrievedChunk,
    UpsertChunksResult,
)
from composition.container import get_container
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("carecontext-retrieval-tools")


@mcp.tool()
def chunk_document(request: ChunkDocumentRequest) -> ChunkDocumentResult:
    """Split document text into retrieval-ready chunks."""
    return get_container().chunking_service.chunk_document(request)


@mcp.tool()
def upsert_chunks(chunks: list[RetrievalDocumentChunk]) -> UpsertChunksResult:
    """Insert or update retrieval-ready chunks in ChromaDB."""
    return get_container().indexing_service.upsert_chunks(chunks)


@mcp.tool()
def hybrid_search(
    query: str,
    top_k: int,
    filters: RetrievalFilter | None = None,
) -> HybridSearchResult:
    """Search chunks with vector similarity plus lightweight keyword scoring."""
    return get_container().retrieval_service.search_chunks(query, top_k, filters)


@mcp.tool()
def rerank_results(
    query: str,
    results: list[RetrievedChunk],
    top_k: int,
) -> RerankResultsResult:
    """Rerank existing retrieval results with deterministic keyword overlap."""
    return get_container().reranking_service.rerank_results(query, results, top_k)


def main() -> None:
    mcp.run(transport=McpTransport.STDIO)


if __name__ == "__main__":
    main()
