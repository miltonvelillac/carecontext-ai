from app.core.config import Settings


def require_supported_provider(provider: str, supported: set[str], provider_type: str) -> str:
    if provider not in supported:
        supported_list = ", ".join(sorted(supported))
        raise ValueError(f"Unsupported {provider_type} provider '{provider}'. Supported: {supported_list}")
    return provider


def validate_provider_settings(settings: Settings) -> None:
    require_supported_provider(settings.llm_provider, {"openai", "mock"}, "LLM")
    require_supported_provider(settings.embeddings_provider, {"openai", "mock"}, "embeddings")
    require_supported_provider(settings.stt_provider, {"openai", "mock"}, "STT")
    require_supported_provider(settings.tts_provider, {"openai", "mock"}, "TTS")

