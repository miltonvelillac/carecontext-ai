from pathlib import Path

from app.adapters.mcp.retrieval_mcp_client import RetrievalMcpClient
from app.composition.container import build_retrieval_tools
from app.core.config import Settings


def test_build_retrieval_tools_uses_retrieval_mcp_client_with_local_chroma_path(
    tmp_path: Path,
) -> None:
    settings = Settings(data_dir=str(tmp_path), chroma_host=None)

    retrieval_tools = build_retrieval_tools(settings)

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.env is not None
    assert retrieval_tools.env["CARECONTEXT_CHROMA_PATH"] == str(tmp_path / "chroma")
    assert "CARECONTEXT_CHROMA_HOST" not in retrieval_tools.env


def test_build_retrieval_tools_uses_configured_chroma_http() -> None:
    settings = Settings(chroma_host="chroma", chroma_port=8000)

    retrieval_tools = build_retrieval_tools(settings)

    assert isinstance(retrieval_tools, RetrievalMcpClient)
    assert retrieval_tools.env is not None
    assert retrieval_tools.env["CARECONTEXT_CHROMA_HOST"] == "chroma"
    assert retrieval_tools.env["CARECONTEXT_CHROMA_PORT"] == "8000"
    assert "CARECONTEXT_CHROMA_PATH" not in retrieval_tools.env
