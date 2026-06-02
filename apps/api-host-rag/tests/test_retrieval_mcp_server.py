import importlib.util
import sys
from pathlib import Path

import pytest
from carecontext_contracts.common import ChromaHnswSpace, LanguageCode, SourceType
from carecontext_contracts.retrieval_mcp import ChunkDocumentRequest, RetrievalFilter


def _load_server_module(module_name: str, relative_path: str):
    server_dir = Path(__file__).resolve().parents[3] / "services" / "retrieval-mcp-server"
    sys.path.insert(0, str(server_dir))
    spec = importlib.util.spec_from_file_location(
        module_name,
        server_dir / relative_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load retrieval {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _chunking_service():
    chunking_service = _load_server_module(
        "retrieval_chunking_service",
        "services/chunking_service.py",
    )
    text_splitter = _load_server_module(
        "retrieval_text_splitter_adapter",
        "adapters/text_splitter.py",
    )
    return chunking_service.ChunkingService(
        text_splitter=text_splitter.LangChainTextSplitterAdapter()
    )


def test_chunk_document_splits_text_and_adds_metadata() -> None:
    service = _chunking_service()
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

    result = service.chunk_document(request)

    assert len(result.chunks) > 1
    assert result.chunks[0].chunk_id == "doc-1-chunk-001"
    assert result.chunks[0].metadata["chunker"] == "recursive_character_text_splitter"
    assert result.chunks[0].metadata["chunk_count"] == str(len(result.chunks))
    assert all(chunk.text for chunk in result.chunks)


class FakeEmbeddingsProvider:
    def embed_text(self, text: str) -> list[float]:
        del text
        return [0.1, 0.2, 0.3]


class CapturingVectorStore:
    collection_name = "test"

    def __init__(self, *, count: int, candidates: list[dict] | None = None) -> None:
        self._count = count
        self.candidates = candidates or []
        self.query_calls: list[dict] = []

    def count(self) -> int:
        return self._count

    def existing_ids(self, ids: list[str]) -> set[str]:
        del ids
        return set()

    def upsert_chunks(self, chunks, embeddings) -> None:
        del chunks, embeddings

    def query_chunks(self, **kwargs) -> list[dict]:
        self.query_calls.append(kwargs)
        return self.candidates


def _retrieval_service(*, vector_store: CapturingVectorStore, candidate_multiplier: int = 5):
    retrieval_service = _load_server_module("retrieval_service", "services/retrieval_service.py")
    settings = _load_server_module("retrieval_settings", "core/settings.py")
    retrievers = _load_server_module("retrieval_retrievers_for_services", "services/retrievers.py")
    return retrieval_service.RetrievalService(
        settings=settings.RetrievalSettings(candidate_multiplier=candidate_multiplier),
        vector_store=vector_store,
        embeddings_provider=FakeEmbeddingsProvider(),
        retriever=retrievers.HybridChunkRetriever(),
    )


def test_search_retrieval_chunks_applies_min_score_threshold() -> None:
    vector_store = CapturingVectorStore(
        count=2,
        candidates=[
            {
                "chunk_id": "good-chunk",
                "document": "Sleep routines support stress management.",
                "metadata": {
                    "doc_id": "doc-1",
                    "chunk_id": "good-chunk",
                    "title": "Sleep Guide",
                    "source_type": "curated",
                    "topic_tags": "sleep",
                    "language": "en",
                },
                "distance": 0.1,
            },
            {
                "chunk_id": "weak-chunk",
                "document": "Unrelated content.",
                "metadata": {
                    "doc_id": "doc-2",
                    "chunk_id": "weak-chunk",
                    "title": "Other Guide",
                    "source_type": "curated",
                    "topic_tags": "other",
                    "language": "en",
                },
                "distance": 0.9,
            },
        ],
    )

    result = _retrieval_service(vector_store=vector_store).search_chunks(
        "sleep stress",
        top_k=2,
        filters=RetrievalFilter(min_score=0.5),
    )

    assert [chunk.chunk_id for chunk in result.results] == ["good-chunk"]


def test_collection_uses_configured_chroma_hnsw_space(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vector_store = _load_server_module("retrieval_vector_store", "adapters/chroma_vector_store.py")
    settings = _load_server_module("retrieval_settings_for_vector_store", "core/settings.py")
    captured: dict[str, object] = {}

    class FakeClient:
        def get_or_create_collection(self, **kwargs):
            captured.update(kwargs)
            return object()

    store = vector_store.ChromaVectorStoreAdapter(
        settings.RetrievalSettings(chroma_hnsw_space=ChromaHnswSpace.INNER_PRODUCT)
    )
    monkeypatch.setattr(store, "_get_client", lambda: FakeClient())

    store._get_collection()

    assert captured["metadata"] == {"hnsw:space": ChromaHnswSpace.INNER_PRODUCT.value}


def test_search_retrieval_chunks_uses_configured_candidate_multiplier() -> None:
    vector_store = CapturingVectorStore(count=100)

    _retrieval_service(vector_store=vector_store, candidate_multiplier=8).search_chunks(
        "sleep stress",
        top_k=3,
    )

    assert vector_store.query_calls[0]["n_results"] == 24


def test_search_retrieval_chunks_passes_supported_metadata_filters_to_chroma() -> None:
    vector_store = CapturingVectorStore(count=100)

    _retrieval_service(vector_store=vector_store).search_chunks(
        "sleep stress",
        top_k=3,
        filters=RetrievalFilter(
            source_types=[SourceType.CURATED, SourceType.UPLOADED],
            topic_tags=["sleep"],
            language=LanguageCode.EN,
        ),
    )

    assert vector_store.query_calls[0]["where"] == {
        "$and": [
            {"language": "en"},
            {"source_type": {"$in": ["curated", "uploaded"]}},
        ]
    }
