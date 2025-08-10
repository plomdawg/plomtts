"""Pydantic models for PlomTTS client."""

from typing import Optional

from pydantic import BaseModel, Field


class VoiceResponse(BaseModel):
    """Response model for voice information."""

    id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Voice name")
    has_transcript: bool = Field(..., description="Whether voice has a transcript file")
    audio_format: str = Field(..., description="Audio file format (mp3, wav, etc.)")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class VoiceListResponse(BaseModel):
    """Response model for listing voices."""

    voices: list[VoiceResponse] = Field(..., description="List of available voices")
    total: int = Field(..., description="Total number of voices")


class TTSRequest(BaseModel):
    """Request model for TTS generation."""

    text: str = Field(
        ..., description="Text to convert to speech", min_length=1, max_length=1000
    )
    voice_id: str = Field(..., description="Voice ID to use for generation")

    # Fish-speech specific parameters
    max_new_tokens: int = Field(0, description="Maximum new tokens (0 for auto)")
    chunk_length: int = Field(200, description="Chunk length for processing")
    top_p: float = Field(0.7, description="Top-p sampling parameter", ge=0.0, le=1.0)
    repetition_penalty: float = Field(
        1.2, description="Repetition penalty", ge=1.0, le=2.0
    )
    temperature: float = Field(
        0.7, description="Temperature for sampling", ge=0.1, le=2.0
    )
    seed: int = Field(0, description="Random seed (0 for random)")


class TTSResponse(BaseModel):
    """Response model for TTS generation."""

    voice_id: str = Field(..., description="Voice ID used")
    text: str = Field(..., description="Generated text")
    audio_format: str = Field(..., description="Audio format (mp3, wav, etc.)")
    duration_seconds: Optional[float] = Field(
        None, description="Audio duration in seconds"
    )


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    fish_speech_status: str = Field(..., description="Fish-speech service status")
    voices_count: int = Field(..., description="Number of available voices")
