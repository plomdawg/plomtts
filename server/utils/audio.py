"""Audio processing utilities."""

import pathlib

from pydub import AudioSegment


def get_audio_duration(file_path: pathlib.Path) -> float:
    """Get audio duration in seconds."""
    try:
        audio = AudioSegment.from_file(str(file_path))
        return len(audio) / 1000.0  # Convert from milliseconds to seconds
    except (FileNotFoundError, OSError, ValueError):
        return 0.0


def get_audio_format(file_path: pathlib.Path) -> str:
    """Get audio format from file extension."""
    return file_path.suffix.lower().lstrip(".")


def validate_audio_file(file_path: pathlib.Path) -> bool:
    """Validate audio file size and format."""
    if not file_path.exists():
        return False

    # Check format
    format_ext = get_audio_format(file_path)
    supported_formats = ["mp3", "wav", "flac", "ogg"]

    return format_ext in supported_formats


def convert_to_format(
    input_path: pathlib.Path,
    output_path: pathlib.Path,
    audio_format: str = "mp3",
) -> bool:
    """Convert audio file to specified format."""
    try:
        audio = AudioSegment.from_file(str(input_path))
        audio.export(str(output_path), format=audio_format)
        return True
    except (FileNotFoundError, OSError, ValueError) as e:
        print(f"❌ Audio conversion failed: {e}")
        return False
