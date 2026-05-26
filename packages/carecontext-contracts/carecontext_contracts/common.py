from enum import StrEnum


class LanguageCode(StrEnum):
    AUTO = "auto"
    EN = "en"
    ES = "es"


class McpTransport(StrEnum):
    STDIO = "stdio"


class RuntimeCommand(StrEnum):
    PYTHON = "python"


class MimeType(StrEnum):
    APPLICATION_PDF = "application/pdf"
    AUDIO_MPEG = "audio/mpeg"


class ProviderName(StrEnum):
    OPENAI = "openai"
    MOCK = "mock"


class ProviderCapability(StrEnum):
    LLM = "LLM"
    EMBEDDINGS = "embeddings"
    STT = "STT"
    TTS = "TTS"


class MetadataKey(StrEnum):
    MOCK = "mock"
    BYTE_COUNT = "byte_count"
    EXTRACTOR = "extractor"
    FILENAME = "filename"
    METADATA_EXTRACTOR = "metadata_extractor"
    PAGE_COUNT = "page_count"
    TEXT_LENGTH = "text_length"
    WARNINGS = "warnings"


class MetadataValue(StrEnum):
    TRUE = "true"
    DOCUMENT_MCP_SERVER = "document-mcp-server"
    PYPDF = "pypdf"
