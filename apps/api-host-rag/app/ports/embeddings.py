from typing import Protocol


class EmbeddingsProvider(Protocol):
    """Strategy port for embedding providers.

    Different embedding backends can be swapped by the composition root while
    retrieval and ingestion code keep depending on this protocol.
    """

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...
