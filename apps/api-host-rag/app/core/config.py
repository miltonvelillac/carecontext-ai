from carecontext_contracts.common import McpTransport, ProviderName, RuntimeCommand
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_title: str = "CareContext AI API"
    api_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "local"
    log_level: str = "INFO"

    llm_provider: ProviderName = ProviderName.MOCK
    embeddings_provider: ProviderName = ProviderName.OPENAI
    stt_provider: ProviderName = ProviderName.OPENAI
    tts_provider: ProviderName = ProviderName.OPENAI

    openai_api_key: str | None = None
    openai_llm_model: str | None = None
    openai_embedding_model: str | None = None
    openai_stt_model: str | None = None
    openai_tts_model: str | None = None

    data_dir: str = "./data"
    chroma_host: str | None = None
    chroma_port: int = 8000

    document_mcp_transport: McpTransport = McpTransport.STDIO
    retrieval_mcp_transport: McpTransport = McpTransport.STDIO
    document_mcp_command: RuntimeCommand = RuntimeCommand.PYTHON
    document_mcp_args: str | None = None
    document_mcp_cwd: str | None = None
    retrieval_mcp_command: RuntimeCommand = RuntimeCommand.PYTHON
    retrieval_mcp_args: str | None = None
    retrieval_mcp_cwd: str | None = None
