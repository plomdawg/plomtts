"""Voice management API endpoints."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from server.core.voice_manager import VoiceManager
from server.models.voice import VoiceListResponse, VoiceResponse

router = APIRouter(prefix="/voices", tags=["voices"])
voice_manager = VoiceManager()


@router.get("", response_model=VoiceListResponse)
async def list_voices():
    """List all available voices."""
    try:
        voices = voice_manager.list_voices()
        return VoiceListResponse(voices=voices, total=len(voices))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list voices: {e}"
        ) from e


@router.get("/{voice_id}", response_model=VoiceResponse)
async def get_voice(voice_id: str):
    """Get details of a specific voice."""
    voice = voice_manager.get_voice(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
    return voice


@router.post("", response_model=VoiceResponse)
async def create_voice(
    name: str = Form(..., description="Voice name"),
    audio: UploadFile = File(..., description="Audio file (MP3, WAV, FLAC, OGG)"),
    transcript: str = Form(None, description="Optional transcript text"),
):
    """Create a new voice from uploaded audio file."""
    try:
        # Validate audio file
        if not audio.filename:
            raise HTTPException(status_code=400, detail="Audio filename is required")

        # Read audio data
        audio_data = await audio.read()
        if not audio_data:
            raise HTTPException(status_code=400, detail="Audio file is empty")

        # Create the voice
        voice = voice_manager.create_voice(
            voice_id=name,
            audio_data=audio_data,
            audio_filename=audio.filename,
            transcript=transcript,
        )

        return voice

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create voice: {e}"
        ) from e


@router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a voice and all its files."""
    if not voice_manager.voice_exists(voice_id):
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")

    try:
        success = voice_manager.delete_voice(voice_id)
        if success:
            return {"message": f"Voice '{voice_id}' deleted successfully"}
        raise HTTPException(
            status_code=500, detail=f"Failed to delete voice '{voice_id}'"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete voice: {e}"
        ) from e
