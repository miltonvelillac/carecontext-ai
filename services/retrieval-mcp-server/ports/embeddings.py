from __future__ import annotations

from typing import Protocol


class EmbeddingsProviderPort(Protocol):
    """Port for embedding text into vector representations."""

    def embed_text(self, text: str) -> list[float]:
        """Return an embedding vector for the provided text."""
        ...
