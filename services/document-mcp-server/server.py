from carecontext_contracts.common import McpTransport, MimeType
from carecontext_contracts.document_mcp import (
    CleanedDocumentText,
    DocumentToolMetadata,
    ExtractedDocument,
)
from document_processing import (
    clean_document_text,
    extract_pdf_text,
    infer_basic_document_metadata,
)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("carecontext-document-tools")


@mcp.tool()
def extract_text_from_pdf(
    content_base64: str,
    filename: str,
    content_type: str | None = MimeType.APPLICATION_PDF,
) -> ExtractedDocument:
    """Extract text and basic metadata from a base64-encoded PDF file."""
    return extract_pdf_text(content_base64, filename, content_type)


@mcp.tool()
def clean_extracted_text(text: str) -> CleanedDocumentText:
    """Normalize extracted document text before chunking and indexing."""
    return clean_document_text(text)


@mcp.tool()
def get_document_metadata(
    text: str,
    filename: str,
    user_title: str | None = None,
) -> DocumentToolMetadata:
    """Infer lightweight metadata from extracted document text."""
    return infer_basic_document_metadata(text, filename, user_title)


def main() -> None:
    mcp.run(transport=McpTransport.STDIO)


if __name__ == "__main__":
    main()
