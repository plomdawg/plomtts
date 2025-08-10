"""Pydantic models for voice management."""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class VoiceCreate(BaseModel):
    """Request model for creating a voice."""

    name: str = Field(..., description="Name of the voice", min_length=1, max_length=50)
    transcript: Optional[str] = Field(None, description="Optional transcript text")


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
