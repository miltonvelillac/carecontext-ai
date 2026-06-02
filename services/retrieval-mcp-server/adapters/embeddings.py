from __future__ import annotations

import hashlib
import math
import re

from carecontext_contracts.retrieval_mcp import RetrievalEmbeddingsProvider
from core.settings import RetrievalSettings
from openai import OpenAI
from ports.embeddings import EmbeddingsProviderPort

DEFAULT_EMBEDDING_DIMENSIONS = 384
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
TOKEN_PATTERN = re.compile(r"[a-zA-Z\u00c0-\u00ff0-9]+")


class DeterministicEmbeddingsProvider:
    def __init__(self, dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS) -> None:
        self.dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in tokenize_text(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class OpenAiEmbeddingsProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_OPENAI_EMBEDDING_MODEL,
        dimensions: int | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self.client = client or OpenAI(api_key=api_key)

    def embed_text(self, text: str) -> list[float]:
        kwargs: dict[str, object] = {
            "model": self.model,
            "input": text,
            "encoding_format": "float",
        }
        if self.dimensions is not None:
            kwargs["dimensions"] = self.dimensions

        response = self.client.embeddings.create(**kwargs)
        return list(response.data[0].embedding)


def build_embeddings_provider(
    settings: RetrievalSettings | None = None,
) -> EmbeddingsProviderPort:
    settings = settings or RetrievalSettings.from_env()

    if settings.embeddings_provider == RetrievalEmbeddingsProvider.DETERMINISTIC:
        return DeterministicEmbeddingsProvider(dimensions=settings.embedding_dimensions)
    if settings.embeddings_provider == RetrievalEmbeddingsProvider.OPENAI:
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when "
                f"CARECONTEXT_EMBEDDINGS_PROVIDER={RetrievalEmbeddingsProvider.OPENAI.value}."
            )
        return OpenAiEmbeddingsProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            dimensions=settings.embedding_dimensions,
        )
    raise ValueError(f"Unsupported embeddings provider '{settings.embeddings_provider}'.")


def tokenize_text(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
