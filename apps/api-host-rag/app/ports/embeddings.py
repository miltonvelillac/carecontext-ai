from typing import Protocol


class EmbeddingsProvider(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

