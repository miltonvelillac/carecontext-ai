import importlib.util
import sys
from pathlib import Path

from carecontext_contracts.common import LanguageCode, SourceType
from carecontext_contracts.retrieval_mcp import RetrievalFilter, RetrievedChunk


def _load_retrievers_module():
    server_dir = Path(__file__).resolve().parents[3] / "services" / "retrieval-mcp-server"
    sys.path.insert(0, str(server_dir))
    spec = importlib.util.spec_from_file_location(
        "retrieval_retrievers",
        server_dir / "retrievers.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load retrieval retrievers.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _candidate(
    *,
    chunk_id: str,
    document: str,
    distance: float,
    topic_tags: str = "sleep",
    language: str = "en",
    source_type: str = "curated",
) -> dict:
    return {
        "chunk_id": chunk_id,
        "document": document,
        "distance": distance,
        "metadata": {
            "doc_id": f"doc-{chunk_id}",
            "chunk_id": chunk_id,
            "title": "Sleep Guide",
            "source_type": source_type,
            "topic_tags": topic_tags,
            "language": language,
            "custom_source": "test",
        },
    }


def test_hybrid_chunk_retriever_filters_by_metadata() -> None:
    retrievers = _load_retrievers_module()
    retriever = retrievers.HybridChunkRetriever()

    ranked = retriever.rank(
        [
            _candidate(chunk_id="match", document="Sleep routines reduce stress.", distance=0.1),
            _candidate(
                chunk_id="wrong-language",
                document="Sleep routines reduce stress.",
                distance=0.0,
                language="es",
            ),
        ],
        "sleep stress",
        RetrievalFilter(
            source_types=[SourceType.CURATED],
            topic_tags=["sleep"],
            language=LanguageCode.EN,
        ),
    )

    assert [chunk.chunk_id for chunk in ranked] == ["match"]


def test_hybrid_chunk_retriever_orders_by_hybrid_score() -> None:
    retrievers = _load_retrievers_module()
    retriever = retrievers.HybridChunkRetriever()

    ranked = retriever.rank(
        [
            _candidate(chunk_id="weak", document="Sleep routines.", distance=0.4),
            _candidate(chunk_id="strong", document="Sleep stress routines.", distance=0.1),
        ],
        "sleep stress",
        None,
    )

    assert [chunk.chunk_id for chunk in ranked] == ["strong", "weak"]
    assert ranked[0].score > ranked[1].score


def test_hybrid_chunk_retriever_applies_min_score_threshold() -> None:
    retrievers = _load_retrievers_module()
    retriever = retrievers.HybridChunkRetriever()
    chunks = [
        RetrievedChunk(
            doc_id="doc-1",
            chunk_id="strong",
            title="Strong",
            snippet="Sleep stress routines.",
            score=0.9,
        ),
        RetrievedChunk(
            doc_id="doc-2",
            chunk_id="weak",
            title="Weak",
            snippet="Unrelated.",
            score=0.2,
        ),
    ]

    filtered = retriever.apply_min_score_threshold(
        chunks,
        RetrievalFilter(min_score=0.5),
    )

    assert [chunk.chunk_id for chunk in filtered] == ["strong"]


def test_hybrid_chunk_retriever_calculates_keyword_overlap() -> None:
    retrievers = _load_retrievers_module()

    score = retrievers.HybridChunkRetriever.keyword_overlap(
        "Sleep routines support stress management.",
        "sleep stress anxiety",
    )

    assert score == 2 / 3
