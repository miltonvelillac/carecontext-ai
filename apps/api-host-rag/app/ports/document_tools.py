from typing import Protocol

from pydantic import BaseModel


class ExtractedDocument(BaseModel):
    text: str
    metadata: dict[str, str]


class DocumentToolsPort(Protocol):
    async def extract_text_from_pdf(self, content: bytes, filename: str) -> ExtractedDocument:
        ...

