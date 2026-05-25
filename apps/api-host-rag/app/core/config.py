from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    environment: str = "local"
    log_level: str = "INFO"

    llm_provider: str = "openai"
    embeddings_provider: str = "openai"
    stt_provider: str = "openai"
    tts_provider: str = "openai"

    openai_api_key: str | None = None
    openai_llm_model: str | None = None
    openai_embedding_model: str | None = None
    openai_stt_model: str | None = None
    openai_tts_model: str | None = None

    data_dir: str = "./data"
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    document_mcp_transport: str = "stdio"
    retrieval_mcp_transport: str = "stdio"

