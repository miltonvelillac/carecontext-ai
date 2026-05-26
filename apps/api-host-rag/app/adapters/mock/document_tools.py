from carecontext_contracts.common import MetadataKey, MetadataValue, MimeType

from app.ports.document_tools import CleanedDocumentText, DocumentToolMetadata, ExtractedDocument
from app.schemas.common import LanguageCode


class MockDocumentTools:
    async def extract_text_from_pdf(
        self,
        content: bytes,
        filename: str,
        content_type: str | None = None,
    ) -> ExtractedDocument:
        return ExtractedDocument(
            text=(
                "Mock extracted PDF text. Consistent sleep routines and reduced evening "
                "stimulation can support sleep quality."
            ),
            filename=filename,
            content_type=content_type or MimeType.APPLICATION_PDF,
            page_count=1,
            metadata={MetadataKey.MOCK: MetadataValue.TRUE, MetadataKey.BYTE_COUNT: str(len(content))},
        )

    async def clean_extracted_text(self, text: str) -> CleanedDocumentText:
        return CleanedDocumentText(text=" ".join(text.split()), warnings=["mock_cleaning"])

    async def get_document_metadata(
        self,
        text: str,
        filename: str,
        user_title: str | None = None,
    ) -> DocumentToolMetadata:
        return DocumentToolMetadata(
            title=user_title or filename,
            language=LanguageCode.EN,
            topic_tags=["sleep", "stress"],
            section_titles=["Sleep routines"],
            quality_score=0.8,
            metadata={MetadataKey.MOCK: MetadataValue.TRUE, MetadataKey.TEXT_LENGTH: str(len(text))},
        )
