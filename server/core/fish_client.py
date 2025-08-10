"""Fish-speech client implementation based on the existing tts_fish.py."""

import pathlib
import shutil
from typing import Optional

from core.config import settings
from gradio_client import Client, handle_file
from utils.audio import convert_to_format


class FishSpeechClient:
    """Client for interacting with fish-speech service."""

    def __init__(self):
        """Initialize the Fish-speech client."""
        self.api_endpoint = settings.fish_speech_url
        print(f"🐟 Initializing Fish-speech client with endpoint: {self.api_endpoint}")

    def _get_reference_audio(
        self, voice_dir: pathlib.Path, voice_name: str
    ) -> pathlib.Path:
        """Get the reference audio file for the voice (prefers WAV for Fish-speech, auto-converts if needed)."""
        # First, try to find WAV file (preferred for Fish-speech)
        wav_file = voice_dir / f"{voice_name}.wav"
        if wav_file.exists():
            print(f"🎵 Using WAV reference audio: {wav_file}")
            return wav_file

        # If no WAV, look for other formats and convert to WAV
        for ext in ["mp3", "flac", "ogg"]:
            source_file = voice_dir / f"{voice_name}.{ext}"
            if source_file.exists():
                print(
                    f"🔄 Converting {ext.upper()} to WAV for Fish-speech compatibility..."
                )
                if convert_to_format(source_file, wav_file, "wav"):
                    print(f"✅ Created WAV version: {wav_file}")
                    return wav_file
                else:
                    print(
                        f"⚠️  Warning: WAV conversion failed, using {ext.upper()} directly"
                    )
                    return source_file

        raise FileNotFoundError(
            f"❌ Reference audio file not found for voice: {voice_name}"
        )

    def generate_audio(self, text: str, voice_id: str, **kwargs) -> pathlib.Path:
        """Generate audio using fish-speech."""
        voice_dir = settings.VOICES_DIR / voice_id
        if not voice_dir.exists():
            raise ValueError(f"❌ Voice not found: {voice_id}")

        # Get the reference audio file (MP3 preferred, supports other formats)
        reference_audio = self._get_reference_audio(voice_dir, voice_id)

        # Read transcript
        reference_transcript = voice_dir / f"{voice_id}.txt"
        if not reference_transcript.exists():
            raise FileNotFoundError(f"❌ Transcript not found for voice: {voice_id}")

        transcript_text = reference_transcript.read_text().strip()

        # Create a new Gradio client for each request
        try:
            client = Client(self.api_endpoint)
        except Exception as e:
            raise RuntimeError(f"❌ Failed to connect to fish-speech service: {e}")

        # Extract parameters with defaults
        max_new_tokens = kwargs.get("max_new_tokens", 0)
        chunk_length = kwargs.get("chunk_length", 200)
        top_p = kwargs.get("top_p", 0.7)
        repetition_penalty = kwargs.get("repetition_penalty", 1.2)
        temperature = kwargs.get("temperature", 0.7)
        seed = kwargs.get("seed", 0)

        # Generate audio using Gradio client
        print(f"🎵 Generating audio for: {text[:50]}...")
        try:
            generated_audio_path, error_message = client.predict(
                text=text,
                reference_id="",
                reference_audio=handle_file(str(reference_audio)),
                reference_text=transcript_text,
                max_new_tokens=max_new_tokens,
                chunk_length=chunk_length,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                temperature=temperature,
                seed=seed,
                use_memory_cache="off",
                api_name="/partial",
            )
        except Exception as e:
            raise RuntimeError(f"❌ Fish-speech API call failed: {e}")

        # Check for errors
        if error_message:
            raise RuntimeError(f"❌ Fish-speech generation failed: {error_message}")

        # Check if the generated audio file exists
        if not generated_audio_path or not pathlib.Path(generated_audio_path).exists():
            raise RuntimeError(
                f"❌ Generated audio file not found: {generated_audio_path}"
            )

        generated_path = pathlib.Path(generated_audio_path)
        print(f"✅ Generated audio: {generated_path}")

        return generated_path

    def generate_audio_to_file(
        self, text: str, voice_id: str, output_path: pathlib.Path, **kwargs
    ) -> pathlib.Path:
        """Generate audio and save to specified path."""
        # Generate the main audio
        generated_audio_path = self.generate_audio(text, voice_id, **kwargs)

        # Copy to output path
        shutil.copy(generated_audio_path, output_path)
        print(f"📁 Saved generated audio to {output_path}")

        return output_path

    async def health_check(self) -> bool:
        """Check if fish-speech service is healthy."""
        try:
            client = Client(self.api_endpoint)
            # Simple test to see if we can connect
            return True
        except Exception as e:
            print(f"❌ Fish-speech health check failed: {e}")
            return False
