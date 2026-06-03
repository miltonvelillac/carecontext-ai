from pathlib import Path

from carecontext_contracts.document_mcp import (
    CleanedDocumentText,
    DocumentToolMetadata,
    ExtractedDocument,
)
from fastapi.testclient import TestClient

from app.api.dependencies import get_document_tools
from app.composition.container import AppContainer
from app.core.config import Settings
from app.main import create_app
from app.schemas.common import LanguageCode


class FakeDocumentTools:
    async def extract_text_from_pdf(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ExtractedDocument:
        return ExtractedDocument(
            text=(
                "Consistent sleep routines, reduced evening stimulation, and regular "
                "wake times can support sleep quality and help manage stress."
            ),
            filename=filename,
            content_type=content_type,
            page_count=1,
            metadata={"source": "fake-document-tools"},
        )

    async def clean_extracted_text(self, text: str) -> CleanedDocumentText:
        return CleanedDocumentText(text=text)

    async def get_document_metadata(
        self,
        text: str,
        filename: str,
        user_title: str | None = None,
    ) -> DocumentToolMetadata:
        return DocumentToolMetadata(
            title=user_title or "Sleep Guide",
            language=LanguageCode.EN,
            topic_tags=["sleep", "stress"],
            section_titles=["Sleep routines"],
            quality_score=0.9,
            metadata={"metadata_source": "fake-document-tools"},
        )


def test_upload_indexes_document_and_text_query_returns_real_citation(tmp_path: Path) -> None:
    app = create_app()
    app.state.settings = Settings(data_dir=str(tmp_path), chroma_host=None)
    app.state.container = AppContainer(app.state.settings)
    app.dependency_overrides[get_document_tools] = lambda: FakeDocumentTools()

    with TestClient(app) as client:
        upload_response = client.post(
            "/api/ingestion/upload",
            files={"file": ("sleep.pdf", b"%PDF fake content", "application/pdf")},
            data={"title": "Sleep Guide", "topic_tags": "sleep,stress", "language": "en"},
        )
        assert upload_response.status_code == 200
        upload_payload = upload_response.json()
        assert upload_payload["doc_id"] == "upload-sleep.pdf"
        assert upload_payload["status"] == "indexed"
        assert upload_payload["document"]["status"] == "indexed"
        assert upload_payload["message"] == "Upload accepted and processed. Inserted chunks: 1."

        documents_response = client.get("/api/documents")
        assert documents_response.status_code == 200
        documents_payload = documents_response.json()

        document_response = client.get("/api/documents/upload-sleep.pdf")
        assert document_response.status_code == 200
        document_payload = document_response.json()

        query_response = client.post(
            "/api/query/text",
            json={
                "query": "How can sleep routines help with stress?",
                "top_k": 5,
                "filters": {
                    "source_types": ["uploaded"],
                    "topic_tags": ["sleep"],
                    "language": "en",
                },
            },
        )
        assert query_response.status_code == 200
        query_payload = query_response.json()

    app.dependency_overrides.clear()

    assert len(documents_payload["documents"]) == 1
    document_summary = documents_payload["documents"][0]
    assert document_summary["doc_id"] == "upload-sleep.pdf"
    assert document_summary["title"] == "Sleep Guide"
    assert document_summary["source_type"] == "uploaded"
    assert document_summary["language"] == "en"
    assert document_summary["status"] == "indexed"
    assert document_summary["topic_tags"] == ["sleep", "stress"]
    assert document_summary["chunk_count"] == 1
    assert document_summary["created_at"] is not None
    assert document_payload["doc_id"] == "upload-sleep.pdf"
    assert document_payload["status"] == "indexed"
    assert document_payload["chunk_count"] == 1
    assert document_payload["chunks"][0]["chunk_id"] == "upload-sleep.pdf-chunk-001"
    assert document_payload["chunks"][0]["created_at"] is not None
    assert document_payload["metadata"]["source"] == "fake-document-tools"
    assert query_payload["citations"]
    assert query_payload["citations"][0]["doc_id"] == "upload-sleep.pdf"
    assert query_payload["citations"][0]["chunk_id"] == "upload-sleep.pdf-chunk-001"
    assert "sleep routines" in query_payload["citations"][0]["snippet"].lower()
    assert query_payload["retrieved_context"][0]["doc_id"] == "upload-sleep.pdf"
    assert "placeholder citation" not in query_payload["answer"].lower()


def test_text_ingestion_indexes_text_and_query_returns_citation(tmp_path: Path) -> None:
    app = create_app()
    app.state.settings = Settings(data_dir=str(tmp_path), chroma_host=None)
    app.state.container = AppContainer(app.state.settings)

    with TestClient(app) as client:
        ingestion_response = client.post(
            "/api/ingestion/text",
            json={
                "title": "Breathing Notes",
                "text": "Slow breathing exercises may help some people reduce acute stress.",
                "topic_tags": ["stress", "breathing"],
                "language": "en",
            },
        )
        assert ingestion_response.status_code == 200
        ingestion_payload = ingestion_response.json()

        query_response = client.post(
            "/api/query/text",
            json={
                "query": "What can help with acute stress?",
                "top_k": 5,
                "filters": {
                    "source_types": ["uploaded"],
                    "topic_tags": ["stress"],
                    "language": "en",
                },
            },
        )
        assert query_response.status_code == 200
        query_payload = query_response.json()

    assert ingestion_payload["status"] == "indexed"
    assert ingestion_payload["doc_id"].startswith("text-breathing-notes-")
    assert query_payload["citations"]
    assert query_payload["citations"][0]["doc_id"].startswith("text-breathing-notes-")
    assert "breathing" in query_payload["citations"][0]["snippet"].lower()
