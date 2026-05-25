from pydantic import BaseModel, Field

from app.schemas.common import LanguageCode


class TranscriptionResult(BaseModel):
    text: str
    language: LanguageCode | None = None
    provider: str | None = None
    model: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)


class TextToSpeechResult(BaseModel):
    audio_id: str | None = None
    audio_url: str | None = None
    content_type: str = "audio/mpeg"
    provider: str | None = None
    model: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)

