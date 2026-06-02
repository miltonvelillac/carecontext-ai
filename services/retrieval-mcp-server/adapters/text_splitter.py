from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter


class LangChainTextSplitterAdapter:
    """Text splitter adapter backed by LangChain."""

    def split_text(
        self,
        text: str,
        *,
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_text(text)
