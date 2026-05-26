from pydantic import BaseModel, Field

from carecontext_contracts.common import MimeType, ProviderName
from app.schemas.common import LanguageCode


class TranscriptionResult(BaseModel):
    text: str
    language: LanguageCode | None = None
    provider: ProviderName | None = None
    model: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)


class TextToSpeechResult(BaseModel):
    audio_id: str | None = None
    audio_url: str | None = None
    content_type: MimeType = MimeType.AUDIO_MPEG
    provider: ProviderName | None = None
    model: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)
