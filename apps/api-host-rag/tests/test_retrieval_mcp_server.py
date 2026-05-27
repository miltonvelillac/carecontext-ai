import importlib.util
import sys
from pathlib import Path

from carecontext_contracts.common import LanguageCode, SourceType
from carecontext_contracts.retrieval_mcp import ChunkDocumentRequest


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
