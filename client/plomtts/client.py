"""PlomTTS Python Client."""

from pathlib import Path
from typing import Any, BinaryIO, Optional, Union
from urllib.parse import urljoin

import requests
from pydantic import ValidationError

from .exceptions import (
    TTSConnectionError,
    TTSError,
    TTSNotFoundError,
    TTSServerError,
    TTSValidationError,
)
from .models import (
    TTSRequest,
    VoiceListResponse,
    VoiceResponse,
)


class TTSClient:
    """Client for interacting with PlomTTS server."""

    def __init__(
        self,
        base_url: str = "http://localhost:8420",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize PlomTTS client.

        Args:
            base_url: Base URL of the PlomTTS server
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Create session with retry configuration
        self.session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=max_retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        try:
            response = self.session.request(
                method=method, url=url, timeout=self.timeout, **kwargs
            )

            # Handle HTTP errors
            if response.status_code == 404:
                raise TTSNotFoundError(
                    f"Resource not found: {response.text}", status_code=404
                )
            if response.status_code == 400:
                raise TTSValidationError(
                    f"Validation error: {response.text}", status_code=400
                )
            if 500 <= response.status_code < 600:
                raise TTSServerError(
                    f"Server error: {response.text}", status_code=response.status_code
                )

            response.raise_for_status()
            return response

        except requests.exceptions.ConnectionError as e:
            raise TTSConnectionError(f"Failed to connect to server: {e}") from e
        except requests.exceptions.Timeout as e:
            raise TTSConnectionError(f"Request timeout: {e}") from e
        except requests.exceptions.RequestException as e:
            raise TTSError(f"Request failed: {e}") from e

    def health(self) -> dict[str, Any]:
        """Check server health status."""
        response = self._make_request("GET", "/health")
        return dict(response.json())

    def list_voices(self) -> VoiceListResponse:
        """List all available voices."""
        response = self._make_request("GET", "/voices")
        try:
            return VoiceListResponse(**response.json())
        except ValidationError as e:
            raise TTSValidationError(f"Invalid response format: {e}") from e

    def get_voice(self, voice_id: str) -> VoiceResponse:
        """Get details of a specific voice."""
        response = self._make_request("GET", f"/voices/{voice_id}")
        try:
            return VoiceResponse(**response.json())
        except ValidationError as e:
            raise TTSValidationError(f"Invalid response format: {e}") from e

    def create_voice(
        self,
        name: str,
        audio: Union[str, Path, BinaryIO, bytes],
        transcript: Optional[str] = None,
        audio_filename: Optional[str] = None,
    ) -> VoiceResponse:
        """Create a new voice from audio file.

        Args:
            name: Voice name/identifier
            audio: Audio file path, Path object, file-like object, or bytes
            transcript: Optional transcript text
            audio_filename: Filename for audio (required if audio is BinaryIO or bytes)
        """
        # Handle different audio input types
        if isinstance(audio, (str, Path)):
            audio_path = Path(audio)
            if not audio_path.exists():
                raise TTSValidationError(f"Audio file not found: {audio}")

            with open(audio_path, "rb") as f:
                audio_data = f.read()
            filename = audio_filename or audio_path.name
        else:
            # Handle file-like object or bytes
            if hasattr(audio, "read"):
                # It's a file-like object
                audio_data = audio.read()
                if hasattr(audio, "seek"):
                    audio.seek(0)  # Reset position for potential reuse
            else:
                # It's bytes
                audio_data = audio

            if not audio_filename:
                raise TTSValidationError(
                    "audio_filename is required when audio is a file-like object or bytes"
                )
            filename = audio_filename

        # Prepare multipart form data
        files = {"audio": (filename, audio_data, "audio/mpeg")}
        data = {"name": name}
        if transcript:
            data["transcript"] = transcript

        response = self._make_request("POST", "/voices", files=files, data=data)
        try:
            return VoiceResponse(**response.json())
        except ValidationError as e:
            raise TTSValidationError(f"Invalid response format: {e}") from e

    def delete_voice(self, voice_id: str) -> dict[str, Any]:
        """Delete a voice."""
        response = self._make_request("DELETE", f"/voices/{voice_id}")
        return dict(response.json())

    def generate_speech(
        self,
        text: str,
        voice_id: str,
        max_new_tokens: int = 0,
        chunk_length: int = 200,
        top_p: float = 0.7,
        repetition_penalty: float = 1.2,
        temperature: float = 0.7,
        seed: int = 0,
    ) -> bytes:  # pylint: disable=too-many-arguments
        """Generate speech and return audio data.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use
            max_new_tokens: Maximum new tokens (0 for auto)
            chunk_length: Chunk length for processing
            top_p: Top-p sampling parameter
            repetition_penalty: Repetition penalty
            temperature: Temperature for sampling
            seed: Random seed (0 for random)

        Returns:
            Audio data as bytes
        """
        # Validate request using Pydantic model
        try:
            request_data = TTSRequest(
                text=text,
                voice_id=voice_id,
                max_new_tokens=max_new_tokens,
                chunk_length=chunk_length,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                temperature=temperature,
                seed=seed,
            )
        except ValidationError as e:
            raise TTSValidationError(f"Invalid request parameters: {e}") from e

        response = self._make_request(
            "POST",
            "/tts",
            json=request_data.model_dump(),
            headers={"Content-Type": "application/json"},
        )

        return response.content

    def save_speech_to_file(
        self, text: str, voice_id: str, output_path: Union[str, Path], **kwargs
    ) -> Path:
        """Generate speech and save to file.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use
            output_path: Path to save audio file
            **kwargs: Additional parameters for generate_speech

        Returns:
            Path to saved file
        """
        audio_data = self.generate_speech(text, voice_id, **kwargs)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(audio_data)

        return output_path

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()
