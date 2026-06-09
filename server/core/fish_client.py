"""Fish Audio S2 client — talks to the self-hosted REST API (`/v1/tts`, msgpack).

Replaces the old Fish-Speech v1.5 Gradio (`/partial`) integration. S2 is driven by a
msgpack POST to `/v1/tts` (schema: ServeTTSRequest). Reference audio is sent inline as
raw bytes and trimmed to a short clip on the fly so over-long voice samples never blow
past the model's 8192-token context.
"""

import pathlib
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request

import msgpack

from server.core.config import settings
from server.utils.audio import convert_to_format

# Fish Audio S2 reference audio should be a short clip (10-30s recommended). Anything
# longer wastes context and risks the 8192-token overflow that crashed v1.5.
REFERENCE_TRIM_SECONDS = 24


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp a value into [lo, hi]."""
    return max(lo, min(hi, value))


class FishSpeechClient:
    """Client for the self-hosted Fish Audio S2 TTS server."""

    def __init__(self):
        """Initialize the Fish Audio S2 client."""
        self.api_endpoint = settings.fish_speech_url
        print(f"🐟 Initializing Fish Audio S2 client with endpoint: {self.api_endpoint}")

    def _get_reference_audio(
        self, voice_dir: pathlib.Path, voice_name: str
    ) -> pathlib.Path:
        """Get reference audio file for voice (prefers WAV, auto-converts if needed)."""
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
                print(
                    f"⚠️  Warning: WAV conversion failed, using {ext.upper()} directly"
                )
                return source_file

        raise FileNotFoundError(
            f"❌ Reference audio file not found for voice: {voice_name}"
        )

    def _reference_bytes(self, reference_audio: pathlib.Path) -> bytes:
        """Trim the reference clip to REFERENCE_TRIM_SECONDS and return WAV bytes.

        S2 clones from a short reference; trimming here means every voice works
        regardless of how long its stored sample is, with no need to touch the
        (LFS-tracked) source files.
        """
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            trimmed = pathlib.Path(tmp.name)
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(reference_audio),
                    "-t", str(REFERENCE_TRIM_SECONDS),
                    "-ac", "1", str(trimmed),
                ],
                capture_output=True,
                check=True,
            )
            return trimmed.read_bytes()
        except subprocess.CalledProcessError:
            # Fall back to the untrimmed file rather than failing outright.
            print("⚠️  Reference trim failed; sending untrimmed audio")
            return reference_audio.read_bytes()
        finally:
            trimmed.unlink(missing_ok=True)

    def _voice_reference(self, voice_id: str) -> dict:
        """Build an S2 reference ({audio, text}) for one voice."""
        voice_dir = settings.VOICES_DIR / voice_id
        if not voice_dir.exists():
            raise ValueError(f"❌ Voice not found: {voice_id}")

        reference_audio = self._get_reference_audio(voice_dir, voice_id)

        reference_transcript = voice_dir / f"{voice_id}.txt"
        if not reference_transcript.exists():
            raise FileNotFoundError(f"❌ Transcript not found for voice: {voice_id}")

        return {
            "audio": self._reference_bytes(reference_audio),
            "text": reference_transcript.read_text().strip(),
        }

    def _post_tts(
        self, text: str, references: list, output_path: pathlib.Path, **kwargs
    ) -> pathlib.Path:
        """POST a ServeTTSRequest to S2 /v1/tts and write the mp3 to output_path."""
        # Map plomtts params onto S2's ServeTTSRequest, clamping to its valid ranges.
        max_new_tokens = kwargs.get("max_new_tokens", 0)
        if max_new_tokens <= 0:
            max_new_tokens = 1024  # S2 default; v1.5 used 0 to mean "auto"
        seed = kwargs.get("seed", 0)

        payload = {
            "text": text,
            "references": references,
            "format": "mp3",
            "chunk_length": int(_clamp(kwargs.get("chunk_length", 200), 100, 300)),
            "max_new_tokens": max_new_tokens,
            "top_p": _clamp(kwargs.get("top_p", 0.8), 0.1, 1.0),
            "repetition_penalty": _clamp(kwargs.get("repetition_penalty", 1.1), 0.9, 2.0),
            "temperature": _clamp(kwargs.get("temperature", 0.8), 0.1, 1.0),
            "seed": seed if seed else None,
            # Same voice → same trimmed reference bytes every call, so caching the
            # encoded reference speeds up repeat requests (e.g. the HA voice).
            "use_memory_cache": "on",
            "normalize": True,
            "streaming": False,
        }

        print(f"🎵 Generating audio for: {text[:60]}...")
        data = msgpack.packb(payload, use_bin_type=True)
        request = urllib.request.Request(
            f"{self.api_endpoint}/v1/tts",
            data=data,
            headers={"Content-Type": "application/msgpack"},
            method="POST",
        )
        try:
            # 300s: a long dialogue (or the first multi-speaker call, which triggers a
            # torch.compile recompile for the new tensor shape) can take ~45s+.
            with urllib.request.urlopen(request, timeout=300) as response:
                output_path.write_bytes(response.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")
            raise RuntimeError(
                f"❌ Fish Audio S2 generation failed ({e.code}): {detail}"
            ) from e
        except Exception as e:
            raise RuntimeError(f"❌ Fish Audio S2 API call failed: {e}") from e

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("❌ Fish Audio S2 returned empty audio")

        print(f"📁 Saved generated audio to {output_path}")
        return output_path

    def generate_audio_to_file(
        self, text: str, voice_id: str, output_path: pathlib.Path, **kwargs
    ) -> pathlib.Path:
        """Generate single-voice speech and write it (mp3) to output_path."""
        reference = self._voice_reference(voice_id)
        return self._post_tts(text, [reference], output_path, **kwargs)

    def generate_dialogue_to_file(
        self, turns: list, output_path: pathlib.Path, **kwargs
    ) -> pathlib.Path:
        """Generate a multi-speaker dialogue and write it (mp3) to output_path.

        `turns` is a list of (voice_id, text) pairs. Each unique voice becomes one S2
        reference; its position is the `<|speaker:N|>` id used to tag that voice's lines,
        so the whole conversation is generated in a single context-aware call.
        """
        references: list = []
        speaker_index: dict = {}
        for voice_id, _ in turns:
            if voice_id not in speaker_index:
                speaker_index[voice_id] = len(references)
                references.append(self._voice_reference(voice_id))

        text = "".join(
            f"<|speaker:{speaker_index[voice_id]}|>{line.strip()}"
            for voice_id, line in turns
        )
        return self._post_tts(text, references, output_path, **kwargs)

    def generate_audio(self, text: str, voice_id: str, **kwargs) -> pathlib.Path:
        """Generate audio and return a path to a temp mp3 (compatibility wrapper)."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = pathlib.Path(tmp.name)
        return self.generate_audio_to_file(text, voice_id, output_path, **kwargs)

    def health_check(self) -> bool:
        """Check if the Fish Audio S2 service is healthy."""
        try:
            with urllib.request.urlopen(
                f"{self.api_endpoint}/v1/health", timeout=5
            ) as response:
                return response.status == 200
        except Exception as e:
            print(f"❌ Fish Audio S2 health check failed: {e}")
            return False
