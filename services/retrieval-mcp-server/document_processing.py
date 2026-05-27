from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Any

import chromadb
from carecontext_contracts.common import LanguageCode
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

COLLECTION_NAME = os.getenv("CARECONTEXT_CHROMA_COLLECTION", "carecontext_chunks")
EMBEDDING_DIMENSIONS = int(os.getenv("CARECONTEXT_EMBEDDING_DIMENSIONS", "384"))
TOKEN_PATTERN = re.compile(r"[a-zA-Z\u00c0-\u00ff0-9]+")


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
        embeddings=[_embed_text(chunk.text) for chunk in chunks_to_write],
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
    if not query.strip() or top_k <= 0:
        return HybridSearchResult()

    collection = _collection()
    collection_size = collection.count()
    if collection_size == 0:
        return HybridSearchResult()

    retrieval_filter = _normalize_filter(filters)
    n_results = min(collection_size, max(top_k * 5, top_k))
    raw_results = collection.query(
        query_embeddings=[_embed_text(query)],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    candidates = _query_candidates(raw_results)
    filtered = [
        candidate
        for candidate in candidates
        if _metadata_matches_filter(candidate["metadata"], retrieval_filter)
    ]
    ranked = sorted(
        (_to_retrieved_chunk(candidate, query) for candidate in filtered),
        key=lambda chunk: chunk.score,
        reverse=True,
    )
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
                rerank_score=_hybrid_score(result.snippet, query, result.score),
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
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )


def _chroma_client() -> Any:
    host = os.getenv("CARECONTEXT_CHROMA_HOST")
    port = os.getenv("CARECONTEXT_CHROMA_PORT")
    if host:
        return chromadb.HttpClient(host=host, port=int(port or "8000"))

    path = os.getenv("CARECONTEXT_CHROMA_PATH", "./data/chroma")
    return chromadb.PersistentClient(path=path)


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


def _metadata_matches_filter(metadata: dict[str, Any], filters: RetrievalFilter | None) -> bool:
    if filters is None:
        return True
    if filters.language != LanguageCode.AUTO and metadata.get("language") != str(filters.language):
        return False
    if filters.source_types and metadata.get("source_type") not in {
        str(source_type) for source_type in filters.source_types
    }:
        return False
    if filters.topic_tags:
        indexed_tags = {
            tag.strip()
            for tag in str(metadata.get("topic_tags", "")).split(",")
            if tag
        }
        if indexed_tags.isdisjoint(set(filters.topic_tags)):
            return False
    return True


def _to_retrieved_chunk(candidate: dict[str, Any], query: str) -> RetrievedChunk:
    metadata = candidate["metadata"]
    document = candidate["document"]
    vector_score = max(0.0, 1.0 - float(candidate["distance"]))
    score = _hybrid_score(document, query, vector_score)
    return RetrievedChunk(
        doc_id=str(metadata.get("doc_id", "")),
        chunk_id=str(metadata.get("chunk_id") or candidate["chunk_id"]),
        title=str(metadata.get("title", "Untitled")),
        snippet=_snippet(document),
        score=round(score, 4),
        section=metadata.get("section"),
        metadata=_public_metadata(metadata),
    )


def _public_metadata(metadata: dict[str, Any]) -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in metadata.items()
        if key not in {"doc_id", "chunk_id", "title", "section"} and value is not None
    }


def _hybrid_score(text: str, query: str, vector_score: float) -> float:
    return (0.75 * vector_score) + (0.25 * _keyword_overlap(text, query))


def _keyword_overlap(text: str, query: str) -> float:
    query_terms = set(_tokens(query))
    if not query_terms:
        return 0.0
    text_terms = set(_tokens(text))
    return len(query_terms & text_terms) / len(query_terms)


def _snippet(text: str, max_length: int = 500) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_length:
        return compact
    return compact[: max_length - 3].rstrip() + "..."


def _embed_text(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for token in _tokens(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
