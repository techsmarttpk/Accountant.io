"""Speech-to-text, behind a provider interface.

The free Google Web Speech API (via `SpeechRecognition`) is fine for local
development but is unofficial, unauthenticated, rate-limited, and not a
choice you'd defend in a production review — it exists here as the default
because it requires no API key to run this repo out of the box. Swapping
to a production STT provider (Whisper API, Google Cloud Speech-to-Text) is
a matter of adding a new class that implements `TranscriptionProvider` and
selecting it via `settings.stt_provider`; nothing else in the codebase
needs to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import speech_recognition as sr

from app.core.exceptions import TranscriptionError


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path | str) -> str: ...


class GoogleWebSpeechProvider(TranscriptionProvider):
    """Free, unofficial, dev-only. NOT for production traffic."""

    def transcribe(self, audio_path: Path | str) -> str:
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(str(audio_path)) as source:
                audio = recognizer.record(source)
        except Exception as exc:
            raise TranscriptionError(f"Could not read audio file: {exc}") from exc

        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError as exc:
            raise TranscriptionError("Could not understand the audio.") from exc
        except sr.RequestError as exc:
            raise TranscriptionError(f"Speech recognition service error: {exc}") from exc


class WhisperProvider(TranscriptionProvider):
    """Placeholder for a production STT provider (e.g. OpenAI Whisper API).

    Not wired up because it requires a paid API key this environment
    doesn't have. Intentionally raises rather than silently degrading —
    selecting `stt_provider=whisper` without implementing this is a
    configuration error that should fail loudly, not fall back quietly.
    """

    def transcribe(self, audio_path: Path | str) -> str:
        raise NotImplementedError(
            "WhisperProvider is not implemented — provide an API key and "
            "implement the call before selecting stt_provider=whisper."
        )


def get_transcription_provider(provider_name: str) -> TranscriptionProvider:
    providers = {
        "google_web": GoogleWebSpeechProvider,
        "whisper": WhisperProvider,
    }
    if provider_name not in providers:
        raise ValueError(f"Unknown STT provider: {provider_name!r}")
    return providers[provider_name]()
