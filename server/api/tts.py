"""TTS generation API endpoints."""

import pathlib
import tempfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from server.core.fish_client import FishSpeechClient
from server.core.voice_manager import VoiceManager
from server.models.tts import TTSRequest
from server.utils.audio import get_audio_duration

router = APIRouter(prefix="/tts", tags=["tts"])
fish_client = FishSpeechClient()
voice_manager = VoiceManager()


@router.post("", response_class=FileResponse)
async def generate_speech(request: TTSRequest):
    """Generate speech from text using specified voice."""
    try:
        # Validate voice exists
        if not voice_manager.voice_exists(request.voice_id):
            raise HTTPException(
                status_code=404, detail=f"Voice '{request.voice_id}' not found"
            )

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            output_path = pathlib.Path(temp_file.name)

        try:
            # Generate audio with fish-speech
            fish_client.generate_audio_to_file(
                text=request.text,
                voice_id=request.voice_id,
                output_path=output_path,
                max_new_tokens=request.max_new_tokens,
                chunk_length=request.chunk_length,
                top_p=request.top_p,
                repetition_penalty=request.repetition_penalty,
                temperature=request.temperature,
                seed=request.seed,
            )

            # Return the audio file
            return FileResponse(
                path=str(output_path),
                media_type="audio/mpeg",
                filename=f"{request.voice_id}_{hash(request.text) % 10000}.mp3",
                headers={
                    "X-Voice-ID": request.voice_id,
                    "X-Text-Length": str(len(request.text)),
                    "X-Audio-Duration": str(get_audio_duration(output_path)),
                },
            )

        except Exception as e:
            # Clean up temp file on error
            if output_path.exists():
                output_path.unlink()
            raise e

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"TTS generation failed: {e}"
        ) from e
