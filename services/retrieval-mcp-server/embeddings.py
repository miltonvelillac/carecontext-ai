from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Protocol

from carecontext_contracts.retrieval_mcp import RetrievalEmbeddingsProvider
from openai import OpenAI

DEFAULT_EMBEDDING_DIMENSIONS = 384
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
TOKEN_PATTERN = re.compile(r"[a-zA-Z\u00c0-\u00ff0-9]+")


class EmbeddingsProvider(Protocol):
    def embed_text(self, text: str) -> list[float]:
        ...


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


def build_embeddings_provider() -> EmbeddingsProvider:
    provider = os.getenv(
        "CARECONTEXT_EMBEDDINGS_PROVIDER",
        RetrievalEmbeddingsProvider.DETERMINISTIC.value,
    ).lower()
    dimensions = int(os.getenv("CARECONTEXT_EMBEDDING_DIMENSIONS", str(DEFAULT_EMBEDDING_DIMENSIONS)))

    if provider == RetrievalEmbeddingsProvider.DETERMINISTIC:
        return DeterministicEmbeddingsProvider(dimensions=dimensions)
    if provider == RetrievalEmbeddingsProvider.OPENAI:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when "
                f"CARECONTEXT_EMBEDDINGS_PROVIDER={RetrievalEmbeddingsProvider.OPENAI.value}."
            )
        return OpenAiEmbeddingsProvider(
            api_key=api_key,
            model=os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_OPENAI_EMBEDDING_MODEL),
            dimensions=dimensions,
        )
    raise ValueError(f"Unsupported embeddings provider '{provider}'.")


def tokenize_text(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
