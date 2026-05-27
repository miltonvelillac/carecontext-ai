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
        assert upload_payload["message"] == "Upload accepted and processed. Inserted chunks: 1."

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

    assert query_payload["citations"]
    assert query_payload["citations"][0]["doc_id"] == "upload-sleep.pdf"
    assert query_payload["citations"][0]["chunk_id"] == "upload-sleep.pdf-chunk-001"
    assert "sleep routines" in query_payload["citations"][0]["snippet"].lower()
    assert query_payload["retrieved_context"][0]["doc_id"] == "upload-sleep.pdf"
    assert "placeholder citation" not in query_payload["answer"].lower()
