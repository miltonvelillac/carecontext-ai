from enum import StrEnum


class LanguageCode(StrEnum):
    AUTO = "auto"
    EN = "en"
    ES = "es"


class SourceType(StrEnum):
    CURATED = "curated"
    UPLOADED = "uploaded"


class McpTransport(StrEnum):
    STDIO = "stdio"


class ChromaHnswSpace(StrEnum):
    COSINE = "cosine"
    L2 = "l2"
    INNER_PRODUCT = "ip"


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
