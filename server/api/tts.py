"""TTS generation API endpoints."""

import pathlib
import tempfile

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from server.core.fish_client import FishSpeechClient
from server.core.voice_manager import VoiceManager
from server.models.tts import MultiTTSRequest, TTSRequest
from server.utils.audio import get_audio_duration

router = APIRouter(prefix="/tts", tags=["tts"])
fish_client = FishSpeechClient()
voice_manager = VoiceManager()

# Fish Audio S2 supports at most this many distinct speakers per dialogue.
MAX_DIALOGUE_SPEAKERS = 5


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


@router.post("/multi", response_class=FileResponse)
async def generate_dialogue(request: MultiTTSRequest):
    """Generate a multi-speaker dialogue from ordered turns (Fish Audio S2)."""
    try:
        # Validate every voice exists and count distinct speakers.
        unique_voices: list[str] = []
        for turn in request.turns:
            if not voice_manager.voice_exists(turn.voice_id):
                raise HTTPException(
                    status_code=404, detail=f"Voice '{turn.voice_id}' not found"
                )
            if turn.voice_id not in unique_voices:
                unique_voices.append(turn.voice_id)

        if len(unique_voices) > MAX_DIALOGUE_SPEAKERS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Too many distinct voices ({len(unique_voices)}); Fish Audio S2 "
                    f"supports at most {MAX_DIALOGUE_SPEAKERS} speakers per dialogue."
                ),
            )

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            output_path = pathlib.Path(temp_file.name)

        try:
            fish_client.generate_dialogue_to_file(
                turns=[(t.voice_id, t.text) for t in request.turns],
                output_path=output_path,
                max_new_tokens=request.max_new_tokens,
                chunk_length=request.chunk_length,
                top_p=request.top_p,
                repetition_penalty=request.repetition_penalty,
                temperature=request.temperature,
                seed=request.seed,
            )

            return FileResponse(
                path=str(output_path),
                media_type="audio/mpeg",
                filename=f"dialogue_{hash(tuple((t.voice_id, t.text) for t in request.turns)) % 10000}.mp3",
                headers={
                    "X-Voices": ",".join(unique_voices),
                    "X-Turns": str(len(request.turns)),
                    "X-Audio-Duration": str(get_audio_duration(output_path)),
                },
            )

        except Exception as e:
            if output_path.exists():
                output_path.unlink()
            raise e

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Dialogue generation failed: {e}"
        ) from e
