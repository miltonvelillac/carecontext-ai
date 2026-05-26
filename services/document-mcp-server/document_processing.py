from __future__ import annotations

import base64
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from carecontext_contracts.common import LanguageCode
from carecontext_contracts.document_mcp import (
    CleanedDocumentText,
    DocumentToolMetadata,
    ExtractedDocument,
)
from pypdf import PdfReader


def _decode_base64(content_base64: str) -> bytes:
    try:
        return base64.b64decode(content_base64, validate=True)
    except ValueError as exc:
        raise ValueError("content_base64 must be valid base64-encoded file bytes") from exc


def _normalize_metadata_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _extract_pdf_metadata(reader: PdfReader) -> dict[str, str]:
    raw_metadata = reader.metadata or {}
    metadata: dict[str, str] = {}
    for key, value in raw_metadata.items():
        normalized_key = str(key).lstrip("/").lower()
        normalized_value = _normalize_metadata_value(value)
        if normalized_key and normalized_value:
            metadata[normalized_key] = normalized_value
    return metadata


def _clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _detect_section_titles(text: str) -> list[str]:
    titles: list[str] = []
    for line in text.splitlines():
        candidate = line.strip().strip("#").strip()
        if not candidate or len(candidate) > 120:
            continue
        is_markdown_heading = line.lstrip().startswith("#")
        numbered_heading_match = re.match(r"^\d+(\.\d+)*[.)]?\s+(.+)", candidate)
        is_numbered_heading = bool(
            numbered_heading_match and numbered_heading_match.group(2)[:1].isupper()
        )
        is_short_title = len(candidate.split()) <= 10 and candidate[:1].isupper()
        if is_markdown_heading or is_numbered_heading or is_short_title:
            titles.append(candidate)
        if len(titles) >= 10:
            break
    return titles


def _quality_score(text: str, page_count: int | None = None) -> float:
    if not text:
        return 0.0
    character_count = len(text)
    if page_count:
        character_count = min(character_count, page_count * 2500)
    return round(min(1.0, character_count / 5000), 2)


def extract_pdf_text(
    content_base64: str,
    filename: str,
    content_type: str | None = "application/pdf",
) -> ExtractedDocument:
    content = _decode_base64(content_base64)
    reader = PdfReader(BytesIO(content))

    page_texts: list[str] = []
    warnings: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        cleaned_page_text = _clean_text(text)
        if cleaned_page_text:
            page_texts.append(f"## Page {index}\n\n{cleaned_page_text}")

    extracted_text = "\n\n".join(page_texts)
    if not extracted_text:
        warnings.append("No text was extracted. The PDF may be scanned or image-only.")

    metadata = _extract_pdf_metadata(reader)
    metadata.update(
        {
            "extractor": "pypdf",
            "filename": filename,
            "page_count": str(len(reader.pages)),
        }
    )
    if warnings:
        metadata["warnings"] = "; ".join(warnings)

    return ExtractedDocument(
        text=extracted_text,
        filename=filename,
        content_type=content_type,
        page_count=len(reader.pages),
        metadata=metadata,
    )


def clean_document_text(text: str) -> CleanedDocumentText:
    cleaned = _clean_text(text)
    warnings: list[str] = []
    if not cleaned:
        warnings.append("Cleaned text is empty.")
    return CleanedDocumentText(
        text=cleaned,
        removed_sections=[],
        warnings=warnings,
    )


def infer_basic_document_metadata(
    text: str,
    filename: str,
    user_title: str | None = None,
) -> DocumentToolMetadata:
    fallback_title = Path(filename).stem or filename
    section_titles = _detect_section_titles(text)
    title = user_title or (section_titles[0] if section_titles else fallback_title)

    return DocumentToolMetadata(
        title=title,
        language=LanguageCode.AUTO,
        topic_tags=[],
        section_titles=section_titles,
        quality_score=_quality_score(text),
        metadata={
            "metadata_extractor": "document-mcp-server",
            "filename": filename,
        },
    )
