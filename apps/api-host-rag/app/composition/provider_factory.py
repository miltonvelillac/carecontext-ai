from carecontext_contracts.common import ProviderCapability, ProviderName

from app.core.config import Settings


def require_supported_provider(
    provider: ProviderName,
    supported: set[ProviderName],
    provider_type: ProviderCapability,
) -> ProviderName:
    if provider not in supported:
        supported_list = ", ".join(sorted(supported))
        raise ValueError(f"Unsupported {provider_type} provider '{provider}'. Supported: {supported_list}")
    return provider


def validate_provider_settings(settings: Settings) -> None:
    supported_providers = {ProviderName.OPENAI, ProviderName.MOCK}
    require_supported_provider(settings.llm_provider, supported_providers, ProviderCapability.LLM)
    require_supported_provider(
        settings.embeddings_provider,
        supported_providers,
        ProviderCapability.EMBEDDINGS,
    )
    require_supported_provider(settings.stt_provider, supported_providers, ProviderCapability.STT)
    require_supported_provider(settings.tts_provider, supported_providers, ProviderCapability.TTS)
