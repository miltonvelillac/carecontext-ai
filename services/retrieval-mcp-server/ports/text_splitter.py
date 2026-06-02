from __future__ import annotations

from typing import Protocol


class TextSplitterPort(Protocol):
    """Port for splitting raw text into retrieval chunks."""

    def split_text(
        self,
        text: str,
        *,
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[str]:
        """Split text into ordered chunk strings."""
        ...
