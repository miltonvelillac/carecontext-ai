from __future__ import annotations

from carecontext_contracts.retrieval_mcp import (
    ChunkDocumentRequest,
    ChunkDocumentResult,
    RetrievalDocumentChunk,
)
from ports.text_splitter import TextSplitterPort


class ChunkingService:
    """Split raw document text into retrieval-ready chunks."""

    def __init__(self, *, text_splitter: TextSplitterPort) -> None:
        self.text_splitter = text_splitter

    def chunk_document(self, request: ChunkDocumentRequest) -> ChunkDocumentResult:
        """Split a document and attach chunk metadata."""

        text = request.text.strip()
        if not text:
            return ChunkDocumentResult()

        chunk_overlap = min(request.chunk_overlap, max(request.chunk_size - 1, 0))
        split_texts = self.text_splitter.split_text(
            text,
            chunk_size=request.chunk_size,
            chunk_overlap=chunk_overlap,
        )
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
