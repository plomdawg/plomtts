"""Configuration management for plomtts."""

import os
from pathlib import Path


class Settings:
    """Application settings."""

    # Server configuration
    HOST: str = os.getenv("PLOMTTS_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PLOMTTS_PORT", "8420"))

    # Fish-speech configuration
    FISH_SPEECH_HOST: str = os.getenv("FISH_SPEECH_HOST", "fish-speech")
    FISH_SPEECH_PORT: int = int(os.getenv("FISH_SPEECH_PORT", "7860"))

    @property
    def fish_speech_url(self) -> str:
        """Get the fish-speech API URL."""
        return f"http://{self.FISH_SPEECH_HOST}:{self.FISH_SPEECH_PORT}"

    # Voice storage
    VOICES_DIR: Path = Path(os.getenv("PLOMTTS_VOICES_DIR", "/app/voices"))

    # Audio processing
    SUPPORTED_AUDIO_FORMATS: list[str] = ["mp3", "wav", "flac", "ogg"]

    def __init__(self):
        """Initialize settings and create directories."""
        self.VOICES_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
