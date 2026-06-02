from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.ports.document_repository import DocumentRepositoryPort
from app.schemas.documents import DocumentChunk, DocumentDetail, DocumentMetadata, DocumentSummary


class LocalJsonDocumentRepository(DocumentRepositoryPort):
    """Persist document read models to a local JSON file for the Docker MVP."""

    def __init__(self, data_dir: str | Path, filename: str = "documents.json") -> None:
        self.path = Path(data_dir) / filename

    async def list_documents(self) -> list[DocumentSummary]:
        documents = self._load_documents()
        summaries = [
            DocumentSummary(
                doc_id=document.doc_id,
                title=document.title,
                source_type=document.source_type,
                language=document.language,
                status=document.status,
                topic_tags=document.topic_tags,
                chunk_count=len(document.chunks),
                created_at=document.created_at,
            )
            for document in documents.values()
        ]
        return sorted(summaries, key=lambda document: document.doc_id)

    async def get_document(self, doc_id: str) -> DocumentDetail | None:
        return self._load_documents().get(doc_id)

    async def save_document(
        self,
        document: DocumentMetadata,
        chunks: list[DocumentChunk],
        metadata: dict[str, str] | None = None,
    ) -> DocumentDetail:
        documents = self._load_documents()
        detail = DocumentDetail(
            doc_id=document.doc_id,
            title=document.title,
            source_type=document.source_type,
            language=document.language,
            status=document.status,
            topic_tags=document.topic_tags,
            chunk_count=len(chunks),
            created_at=document.created_at,
            chunks=chunks,
            metadata=metadata or {},
        )
        documents[document.doc_id] = detail
        self._save_documents(documents)
        return detail

    def _load_documents(self) -> dict[str, DocumentDetail]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, dict):
            return {}
        raw_documents = payload.get("documents", {})
        if not isinstance(raw_documents, dict):
            return {}
        return {
            doc_id: DocumentDetail.model_validate(raw_document)
            for doc_id, raw_document in raw_documents.items()
            if isinstance(raw_document, dict)
        }

    def _save_documents(self, documents: dict[str, DocumentDetail]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "documents": {
                doc_id: document.model_dump(mode="json")
                for doc_id, document in documents.items()
            }
        }
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, sort_keys=True)
            file.write("\n")
