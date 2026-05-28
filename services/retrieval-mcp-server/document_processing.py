from __future__ import annotations

import os
from typing import Any

import chromadb
from carecontext_contracts.common import ChromaHnswSpace
from carecontext_contracts.retrieval_mcp import (
    ChunkDocumentRequest,
    ChunkDocumentResult,
    HybridSearchResult,
    RerankResultsResult,
    RerankedChunk,
    RetrievalDocumentChunk,
    RetrievalFilter,
    RetrievedChunk,
    UpsertChunksResult,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from embeddings import build_embeddings_provider
from retrievers import HybridChunkRetriever

COLLECTION_NAME = os.getenv("CARECONTEXT_CHROMA_COLLECTION", "carecontext_chunks")
DEFAULT_CHROMA_HNSW_SPACE = ChromaHnswSpace.COSINE
DEFAULT_CANDIDATE_MULTIPLIER = 5


def chunk_retrieval_document(request: ChunkDocumentRequest) -> ChunkDocumentResult:
    text = request.text.strip()
    if not text:
        return ChunkDocumentResult()

    chunk_overlap = min(request.chunk_overlap, max(request.chunk_size - 1, 0))
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=request.chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    split_texts = splitter.split_text(text)
    chunk_count = len(split_texts)
    chunks = [
        RetrievalDocumentChunk(
            doc_id=request.doc_id,
            chunk_id=f"{request.doc_id}-chunk-{index:03d}",
            title=request.title,
            text=chunk_text,
            source_type=request.source_type,
            topic_tags=request.topic_tags,
            language=request.language,
            section=request.section,
            quality_score=request.quality_score,
            metadata={
                **request.metadata,
                "chunk_index": str(index),
                "chunk_count": str(chunk_count),
                "chunker": "recursive_character_text_splitter",
            },
        )
        for index, chunk_text in enumerate(split_texts, start=1)
    ]
    return ChunkDocumentResult(chunks=chunks)


def upsert_retrieval_chunks(chunks: list[RetrievalDocumentChunk]) -> UpsertChunksResult:
    normalized_chunks = _normalize_chunks(chunks)
    if not normalized_chunks:
        return UpsertChunksResult(
            inserted_count=0,
            skipped_count=0,
            collection_name=COLLECTION_NAME,
        )

    chunk_by_id = {chunk.chunk_id: chunk for chunk in normalized_chunks if chunk.text.strip()}
    skipped_count = len(normalized_chunks) - len(chunk_by_id)
    if not chunk_by_id:
        return UpsertChunksResult(
            inserted_count=0,
            skipped_count=skipped_count,
            collection_name=COLLECTION_NAME,
        )

    collection = _collection()
    ids = list(chunk_by_id)
    existing_ids = _existing_ids(collection, ids)
    chunks_to_write = list(chunk_by_id.values())

    collection.upsert(
        ids=ids,
        embeddings=[_embeddings_provider().embed_text(chunk.text) for chunk in chunks_to_write],
        documents=[chunk.text for chunk in chunks_to_write],
        metadatas=[_chunk_metadata(chunk) for chunk in chunks_to_write],
    )

    updated_count = len(existing_ids)
    inserted_count = len(ids) - updated_count
    return UpsertChunksResult(
        inserted_count=inserted_count,
        updated_count=updated_count,
        skipped_count=skipped_count,
        collection_name=COLLECTION_NAME,
    )


def search_retrieval_chunks(
    query: str,
    top_k: int,
    filters: RetrievalFilter | None = None,
) -> HybridSearchResult:
    """Search indexed chunks and return the best retrieval candidates for a query."""

    # Guard clause: empty queries or non-positive limits should not hit Chroma.
    if not query.strip() or top_k <= 0:
        return HybridSearchResult()

    # Open the configured Chroma collection and skip retrieval when it has no chunks.
    collection = _collection()
    collection_size = collection.count()
    if collection_size == 0:
        return HybridSearchResult()

    # Normalize dict filters into the shared contract model so downstream code
    # can read language, metadata filters, and min_score consistently.
    retrieval_filter = _normalize_filter(filters)

    # Ask Chroma for a candidate pool larger than top_k. Chroma ranks these by
    # vector distance only; the app reranks them later with hybrid scoring.
    n_results = min(collection_size, top_k * _candidate_multiplier())
    raw_results = collection.query(
        query_embeddings=[_embeddings_provider().embed_text(query)],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    # Convert Chroma's column-oriented response into per-candidate dictionaries:
    # chunk_id, document text, metadata, and vector distance.
    candidates = _query_candidates(raw_results)

    # Apply metadata filters, compute hybrid scores, sort by relevance, and
    # apply the optional min_score threshold.
    ranked = HybridChunkRetriever().rank(candidates, query, retrieval_filter)

    # Return at most top_k chunks after reranking and threshold filtering.
    return HybridSearchResult(results=ranked[:top_k])


def rerank_retrieval_results(
    query: str,
    results: list[RetrievedChunk],
    top_k: int,
) -> RerankResultsResult:
    if top_k <= 0:
        return RerankResultsResult()

    normalized_results = [
        result if isinstance(result, RetrievedChunk) else RetrievedChunk.model_validate(result)
        for result in results
    ]
    reranked = sorted(
        (
            RerankedChunk(
                chunk=result,
                rerank_score=HybridChunkRetriever.hybrid_score(
                    result.snippet,
                    query,
                    result.score,
                ),
                reason="vector_score_plus_keyword_overlap",
            )
            for result in normalized_results
        ),
        key=lambda item: item.rerank_score,
        reverse=True,
    )
    return RerankResultsResult(results=reranked[:top_k])


def _collection() -> Any:
    client = _chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": _chroma_hnsw_space().value},
        embedding_function=None,
    )


def _chroma_client() -> Any:
    host = os.getenv("CARECONTEXT_CHROMA_HOST")
    port = os.getenv("CARECONTEXT_CHROMA_PORT")
    if host:
        return chromadb.HttpClient(host=host, port=int(port or "8000"))

    path = os.getenv("CARECONTEXT_CHROMA_PATH", "./data/chroma")
    return chromadb.PersistentClient(path=path)


def _chroma_hnsw_space() -> ChromaHnswSpace:
    return ChromaHnswSpace(
        os.getenv("CARECONTEXT_CHROMA_HNSW_SPACE", DEFAULT_CHROMA_HNSW_SPACE.value)
    )


def _embeddings_provider() -> Any:
    return build_embeddings_provider()


def _candidate_multiplier() -> int:
    return max(
        1,
        int(
            os.getenv(
                "CARECONTEXT_RETRIEVAL_CANDIDATE_MULTIPLIER",
                str(DEFAULT_CANDIDATE_MULTIPLIER),
            )
        ),
    )


def _normalize_chunks(
    chunks: list[dict[str, Any]] | list[RetrievalDocumentChunk],
) -> list[RetrievalDocumentChunk]:
    return [
        chunk
        if isinstance(chunk, RetrievalDocumentChunk)
        else RetrievalDocumentChunk.model_validate(chunk)
        for chunk in chunks
    ]


def _normalize_filter(filters: dict[str, Any] | RetrievalFilter | None) -> RetrievalFilter | None:
    if filters is None:
        return None
    return filters if isinstance(filters, RetrievalFilter) else RetrievalFilter.model_validate(filters)


def _existing_ids(collection: Any, ids: list[str]) -> set[str]:
    try:
        existing = collection.get(ids=ids, include=[])
    except Exception:
        return set()
    return set(existing.get("ids", []))


def _chunk_metadata(chunk: RetrievalDocumentChunk) -> dict[str, str | int | float | bool]:
    metadata: dict[str, str | int | float | bool] = {
        "doc_id": chunk.doc_id,
        "chunk_id": chunk.chunk_id,
        "title": chunk.title,
        "source_type": str(chunk.source_type),
        "topic_tags": ",".join(chunk.topic_tags),
        "language": str(chunk.language),
    }
    if chunk.section is not None:
        metadata["section"] = chunk.section
    if chunk.created_at is not None:
        metadata["created_at"] = chunk.created_at.isoformat()
    if chunk.quality_score is not None:
        metadata["quality_score"] = chunk.quality_score

    for key, value in chunk.metadata.items():
        if value is not None:
            metadata[f"custom_{key}"] = str(value)
    return metadata


def _query_candidates(raw_results: dict[str, Any]) -> list[dict[str, Any]]:
    ids = raw_results.get("ids", [[]])[0]
    documents = raw_results.get("documents", [[]])[0]
    metadatas = raw_results.get("metadatas", [[]])[0]
    distances = raw_results.get("distances", [[]])[0]
    candidates: list[dict[str, Any]] = []
    for index, chunk_id in enumerate(ids):
        candidates.append(
            {
                "chunk_id": chunk_id,
                "document": documents[index] or "",
                "metadata": metadatas[index] or {},
                "distance": distances[index],
            }
        )
    return candidates
