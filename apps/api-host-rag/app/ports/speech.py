from typing import Protocol

from pydantic import BaseModel


class TranscriptionResult(BaseModel):
    text: str
    language: str | None = None


class AudioResult(BaseModel):
    audio: bytes
    content_type: str


class SpeechToTextProvider(Protocol):
    """Strategy port for speech-to-text providers."""

    async def transcribe(self, audio: bytes, content_type: str) -> TranscriptionResult:
        ...


class TextToSpeechProvider(Protocol):
    """Strategy port for text-to-speech providers."""

    async def synthesize(self, text: str, voice: str | None = None) -> AudioResult:
        ...
