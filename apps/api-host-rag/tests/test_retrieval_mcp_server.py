import importlib.util
import sys
from pathlib import Path

import pytest
from carecontext_contracts.common import ChromaHnswSpace, LanguageCode, SourceType
from carecontext_contracts.retrieval_mcp import ChunkDocumentRequest, RetrievalFilter


def _load_retrieval_processing_module():
    server_dir = Path(__file__).resolve().parents[3] / "services" / "retrieval-mcp-server"
    sys.path.insert(0, str(server_dir))
    spec = importlib.util.spec_from_file_location(
        "retrieval_document_processing",
        server_dir / "document_processing.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load retrieval document_processing.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_chunk_retrieval_document_splits_text_and_adds_metadata() -> None:
    processing = _load_retrieval_processing_module()
    request = ChunkDocumentRequest(
        doc_id="doc-1",
        title="Sleep Basics",
        text="Sleep routines support rest. " * 20,
        source_type=SourceType.CURATED,
        topic_tags=["sleep"],
        language=LanguageCode.EN,
        section="Sleep routines",
        metadata={"source": "test"},
        chunk_size=120,
        chunk_overlap=20,
    )

    result = processing.chunk_retrieval_document(request)

    assert len(result.chunks) > 1
    assert result.chunks[0].chunk_id == "doc-1-chunk-001"
    assert result.chunks[0].metadata["chunker"] == "recursive_character_text_splitter"
    assert result.chunks[0].metadata["chunk_count"] == str(len(result.chunks))
    assert all(chunk.text for chunk in result.chunks)


def test_search_retrieval_chunks_applies_min_score_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processing = _load_retrieval_processing_module()

    class FakeCollection:
        def count(self) -> int:
            return 2

        def query(self, **kwargs):
            del kwargs
            return {
                "ids": [["good-chunk", "weak-chunk"]],
                "documents": [["Sleep routines support stress management.", "Unrelated content."]],
                "metadatas": [[
                    {
                        "doc_id": "doc-1",
                        "chunk_id": "good-chunk",
                        "title": "Sleep Guide",
                        "source_type": "curated",
                        "topic_tags": "sleep",
                        "language": "en",
                    },
                    {
                        "doc_id": "doc-2",
                        "chunk_id": "weak-chunk",
                        "title": "Other Guide",
                        "source_type": "curated",
                        "topic_tags": "other",
                        "language": "en",
                    },
                ]],
                "distances": [[0.1, 0.9]],
            }

    class FakeEmbeddingsProvider:
        def embed_text(self, text: str) -> list[float]:
            del text
            return [0.1, 0.2, 0.3]

    monkeypatch.setattr(processing, "_collection", lambda: FakeCollection())
    monkeypatch.setattr(processing, "_embeddings_provider", lambda: FakeEmbeddingsProvider())

    result = processing.search_retrieval_chunks(
        "sleep stress",
        top_k=2,
        filters=RetrievalFilter(min_score=0.5),
    )

    assert [chunk.chunk_id for chunk in result.results] == ["good-chunk"]


def test_collection_uses_configured_chroma_hnsw_space(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processing = _load_retrieval_processing_module()
    captured: dict[str, object] = {}

    class FakeClient:
        def get_or_create_collection(self, **kwargs):
            captured.update(kwargs)
            return object()

    monkeypatch.setenv(
        "CARECONTEXT_CHROMA_HNSW_SPACE",
        ChromaHnswSpace.INNER_PRODUCT.value,
    )
    monkeypatch.setattr(processing, "_chroma_client", lambda: FakeClient())

    processing._collection()

    assert captured["metadata"] == {"hnsw:space": ChromaHnswSpace.INNER_PRODUCT.value}


def test_search_retrieval_chunks_uses_configured_candidate_multiplier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processing = _load_retrieval_processing_module()
    captured: dict[str, object] = {}

    class FakeCollection:
        def count(self) -> int:
            return 100

        def query(self, **kwargs):
            captured.update(kwargs)
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]],
            }

    class FakeEmbeddingsProvider:
        def embed_text(self, text: str) -> list[float]:
            del text
            return [0.1, 0.2, 0.3]

    monkeypatch.setenv("CARECONTEXT_RETRIEVAL_CANDIDATE_MULTIPLIER", "8")
    monkeypatch.setattr(processing, "_collection", lambda: FakeCollection())
    monkeypatch.setattr(processing, "_embeddings_provider", lambda: FakeEmbeddingsProvider())

    processing.search_retrieval_chunks("sleep stress", top_k=3)

    assert captured["n_results"] == 24
