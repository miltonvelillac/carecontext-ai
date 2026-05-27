from carecontext_contracts.common import McpTransport
from carecontext_contracts.retrieval_mcp import (
    HybridSearchResult,
    RerankResultsResult,
    RetrievalDocumentChunk,
    RetrievalFilter,
    RetrievedChunk,
    UpsertChunksResult,
)
from document_processing import (
    rerank_retrieval_results,
    search_retrieval_chunks,
    upsert_retrieval_chunks,
)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("carecontext-retrieval-tools")


@mcp.tool()
def upsert_chunks(chunks: list[RetrievalDocumentChunk]) -> UpsertChunksResult:
    """Insert or update retrieval-ready chunks in ChromaDB."""
    return upsert_retrieval_chunks(chunks)


@mcp.tool()
def hybrid_search(
    query: str,
    top_k: int,
    filters: RetrievalFilter | None = None,
) -> HybridSearchResult:
    """Search chunks with vector similarity plus lightweight keyword scoring."""
    return search_retrieval_chunks(query, top_k, filters)


@mcp.tool()
def rerank_results(
    query: str,
    results: list[RetrievedChunk],
    top_k: int,
) -> RerankResultsResult:
    """Rerank existing retrieval results with deterministic keyword overlap."""
    return rerank_retrieval_results(query, results, top_k)


def main() -> None:
    mcp.run(transport=McpTransport.STDIO)


if __name__ == "__main__":
    main()
