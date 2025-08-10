"""Voice management functionality."""

import pathlib
import shutil
from datetime import datetime
from typing import List, Optional

from server.core.config import settings
from server.utils.audio import convert_to_format, get_audio_format, validate_audio_file
from shared.models import VoiceResponse


class VoiceManager:
    """Manages voice models and files."""

    def __init__(self):
        """Initialize voice manager."""
        self.voices_dir = settings.VOICES_DIR
        self.voices_dir.mkdir(parents=True, exist_ok=True)

    def list_voices(self) -> List[VoiceResponse]:
        """List all available voices."""
        voices = []

        for voice_dir in self.voices_dir.iterdir():
            if not voice_dir.is_dir():
                continue

            # Look for audio files
            audio_file = None
            for ext in settings.SUPPORTED_AUDIO_FORMATS:
                potential_file = voice_dir / f"{voice_dir.name}.{ext}"
                if potential_file.exists():
                    audio_file = potential_file
                    break

            if not audio_file:
                print(f"⚠️  Skipping {voice_dir.name}: no audio file found")
                continue

            # Check for transcript
            transcript_file = voice_dir / f"{voice_dir.name}.txt"
            has_transcript = transcript_file.exists()

            # Get creation time (use directory creation time)
            try:
                created_at = datetime.fromtimestamp(
                    voice_dir.stat().st_ctime
                ).isoformat()
            except (OSError, ValueError):
                created_at = None

            voice = VoiceResponse(
                id=voice_dir.name,
                name=voice_dir.name,
                has_transcript=has_transcript,
                audio_format=get_audio_format(audio_file),
                created_at=created_at,
            )
            voices.append(voice)

        return sorted(voices, key=lambda v: v.name)

    def get_voice(self, voice_id: str) -> Optional[VoiceResponse]:
        """Get a specific voice by ID."""
        voices = self.list_voices()
        for voice in voices:
            if voice.id == voice_id:
                return voice
        return None

    def create_voice(
        self,
        voice_id: str,
        audio_data: bytes,
        audio_filename: str,
        transcript: Optional[str] = None,
    ) -> VoiceResponse:
        """Create a new voice from audio data."""
        # Validate voice ID
        if not voice_id or not voice_id.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "❌ Voice ID must contain only letters, numbers, hyphens, and underscores"
            )

        # Create voice directory
        voice_dir = self.voices_dir / voice_id
        if voice_dir.exists():
            raise ValueError(f"❌ Voice '{voice_id}' already exists")

        voice_dir.mkdir(parents=True)

        try:
            # Determine audio format from filename
            audio_path = pathlib.Path(audio_filename)
            audio_format = get_audio_format(audio_path)

            if audio_format not in settings.SUPPORTED_AUDIO_FORMATS:
                raise ValueError(f"❌ Unsupported audio format: {audio_format}")

            # Save audio file
            audio_file_path = voice_dir / f"{voice_id}.{audio_format}"
            with open(audio_file_path, "wb") as f:
                f.write(audio_data)

            # Validate the saved audio file
            if not validate_audio_file(audio_file_path):
                raise ValueError("❌ Audio file validation failed")

            # Save transcript if provided
            if transcript:
                transcript_file = voice_dir / f"{voice_id}.txt"
                transcript_file.write_text(transcript.strip())
                print(f"📝 Saved transcript to {transcript_file}")
            else:
                print("⚠️  No transcript provided - you'll need to add one manually")

            # 🎵 Create WAV version for Fish-speech compatibility
            wav_file_path = voice_dir / f"{voice_id}.wav"
            if audio_format != "wav":
                print(
                    f"🔄 Converting {audio_format.upper()} to WAV for Fish-speech compatibility..."
                )
                if convert_to_format(audio_file_path, wav_file_path, "wav"):
                    print(f"✅ Created WAV version: {wav_file_path}")
                else:
                    print(
                        f"⚠️  Warning: Failed to create WAV version, Fish-speech may not work properly"
                    )

            print(f"✅ Created voice '{voice_id}' with audio format: {audio_format}")

            # Return the created voice
            return VoiceResponse(
                id=voice_id,
                name=voice_id,
                has_transcript=transcript is not None,
                audio_format=audio_format,
                created_at=datetime.now().isoformat(),
            )

        except Exception as e:
            # Clean up on failure
            if voice_dir.exists():
                shutil.rmtree(voice_dir)
            raise e

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a voice and all its files."""
        voice_dir = self.voices_dir / voice_id

        if not voice_dir.exists():
            return False

        try:
            shutil.rmtree(voice_dir)
            print(f"🗑️  Deleted voice '{voice_id}'")
            return True
        except (OSError, PermissionError) as e:
            print(f"❌ Failed to delete voice '{voice_id}': {e}")
            return False

    def voice_exists(self, voice_id: str) -> bool:
        """Check if a voice exists."""
        return (self.voices_dir / voice_id).is_dir()
