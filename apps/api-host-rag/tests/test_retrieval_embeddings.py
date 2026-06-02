import importlib.util
import sys
from pathlib import Path

import pytest
from carecontext_contracts.retrieval_mcp import RetrievalEmbeddingsProvider


class FakeEmbedding:
    embedding = [0.1, 0.2, 0.3]


class FakeEmbeddingResponse:
    data = [FakeEmbedding()]


class FakeEmbeddingsResource:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeEmbeddingResponse()


class FakeOpenAiClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsResource()


def _load_embeddings_module():
    server_dir = Path(__file__).resolve().parents[3] / "services" / "retrieval-mcp-server"
    sys.path.insert(0, str(server_dir))
    spec = importlib.util.spec_from_file_location(
        "retrieval_embeddings",
        server_dir / "adapters" / "embeddings.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load retrieval embeddings.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deterministic_embeddings_provider_returns_configured_dimensions() -> None:
    embeddings = _load_embeddings_module()
    provider = embeddings.DeterministicEmbeddingsProvider(dimensions=8)

    vector = provider.embed_text("sleep stress sleep")

    assert len(vector) == 8
    assert any(value != 0.0 for value in vector)


def test_openai_embeddings_provider_calls_embeddings_api() -> None:
    embeddings = _load_embeddings_module()
    client = FakeOpenAiClient()
    provider = embeddings.OpenAiEmbeddingsProvider(
        api_key="test-key",
        model="text-embedding-test",
        dimensions=3,
        client=client,
    )

    vector = provider.embed_text("sleep routines")

    assert vector == [0.1, 0.2, 0.3]
    assert client.embeddings.calls == [
        {
            "model": "text-embedding-test",
            "input": "sleep routines",
            "encoding_format": "float",
            "dimensions": 3,
        }
    ]


def test_build_embeddings_provider_requires_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    embeddings = _load_embeddings_module()
    monkeypatch.setenv(
        "CARECONTEXT_EMBEDDINGS_PROVIDER",
        RetrievalEmbeddingsProvider.OPENAI.value,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
        embeddings.build_embeddings_provider()
