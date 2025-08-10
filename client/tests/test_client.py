"""Comprehensive tests for PlomTTS client."""

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import responses
from requests.exceptions import ConnectionError, Timeout

from plomtts import (
    TTSClient,
    TTSConnectionError,
    TTSNotFoundError,
    TTSServerError,
    TTSValidationError,
    VoiceListResponse,
    VoiceResponse,
)


@pytest.fixture
def client():
    """Create test client."""
    return TTSClient(base_url="http://localhost:8420", timeout=10.0)


@pytest.fixture
def mock_voice_response():
    """Mock voice response data."""
    return {
        "id": "test_voice",
        "name": "Test Voice",
        "has_transcript": True,
        "audio_format": "mp3",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_voice_list_response(mock_voice_response):
    """Mock voice list response data."""
    return {"voices": [mock_voice_response], "total": 1}


@pytest.fixture
def mock_tts_response():
    """Mock TTS response data."""
    return {
        "voice_id": "test_voice",
        "text": "Hello world",
        "audio_format": "mp3",
        "duration_seconds": 2.5,
    }


@pytest.fixture
def sample_audio_data():
    """Sample audio data for testing."""
    # Read the actual arnold.mp3 file
    arnold_mp3_path = Path(__file__).parent / "arnold.mp3"
    if arnold_mp3_path.exists():
        return arnold_mp3_path.read_bytes()
    else:
        # Fallback to fake data if file doesn't exist
        return b"fake_mp3_data_for_testing"


@pytest.fixture
def arnold_transcript():
    """Arnold transcript text for testing."""
    # Read the actual arnold.txt file
    arnold_txt_path = Path(__file__).parent / "arnold.txt"
    if arnold_txt_path.exists():
        return arnold_txt_path.read_text(encoding="utf-8").strip()
    else:
        # Fallback to simple text if file doesn't exist
        return "Hello world"


class TestTTSClient:
    """Test PlomTTS client functionality."""

    def test_client_initialization(self):
        """Test client initialization with different parameters."""
        # Default initialization
        client = TTSClient()
        assert client.base_url == "http://localhost:8420"
        assert client.timeout == 30.0
        assert client.max_retries == 3

        # Custom initialization
        client = TTSClient(
            base_url="http://example.com:9000/", timeout=10.0, max_retries=5
        )
        assert client.base_url == "http://example.com:9000"
        assert client.timeout == 10.0
        assert client.max_retries == 5

    @responses.activate
    def test_health_check(self, client):
        """Test health check endpoint."""
        responses.add(
            responses.GET,
            "http://localhost:8420/health",
            json={"status": "ok"},
            status=200,
        )

        result = client.health()
        assert result == {"status": "ok"}

    @responses.activate
    def test_list_voices_success(self, client, mock_voice_list_response):
        """Test successful voice listing."""
        responses.add(
            responses.GET,
            "http://localhost:8420/voices",
            json=mock_voice_list_response,
            status=200,
        )

        result = client.list_voices()
        assert isinstance(result, VoiceListResponse)
        assert result.total == 1
        assert len(result.voices) == 1
        assert result.voices[0].id == "test_voice"

    @responses.activate
    def test_list_voices_empty(self, client):
        """Test listing voices when none exist."""
        responses.add(
            responses.GET,
            "http://localhost:8420/voices",
            json={"voices": [], "total": 0},
            status=200,
        )

        result = client.list_voices()
        assert isinstance(result, VoiceListResponse)
        assert result.total == 0
        assert len(result.voices) == 0

    @responses.activate
    def test_get_voice_success(self, client, mock_voice_response):
        """Test successful voice retrieval."""
        responses.add(
            responses.GET,
            "http://localhost:8420/voices/test_voice",
            json=mock_voice_response,
            status=200,
        )

        result = client.get_voice("test_voice")
        assert isinstance(result, VoiceResponse)
        assert result.id == "test_voice"
        assert result.name == "Test Voice"
        assert result.has_transcript is True

    @responses.activate
    def test_get_voice_not_found(self, client):
        """Test voice not found error."""
        responses.add(
            responses.GET,
            "http://localhost:8420/voices/nonexistent",
            json={"detail": "Voice 'nonexistent' not found"},
            status=404,
        )

        with pytest.raises(TTSNotFoundError) as exc_info:
            client.get_voice("nonexistent")
        assert exc_info.value.status_code == 404

    @responses.activate
    def test_create_voice_from_file_path(
        self,
        client,
        mock_voice_response,
        tmp_path,
        sample_audio_data,
        arnold_transcript,
    ):
        """Test creating voice from file path."""
        # Create temporary audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(sample_audio_data)

        responses.add(
            responses.POST,
            "http://localhost:8420/voices",
            json=mock_voice_response,
            status=200,
        )

        result = client.create_voice(
            name="test_voice", audio=str(audio_file), transcript=arnold_transcript
        )

        assert isinstance(result, VoiceResponse)
        assert result.id == "test_voice"

        # Check the request was made correctly
        request = responses.calls[0].request
        assert "multipart/form-data" in request.headers["Content-Type"]

    @responses.activate
    def test_create_voice_from_file_object(
        self, client, mock_voice_response, sample_audio_data
    ):
        """Test creating voice from file object."""
        audio_file = io.BytesIO(sample_audio_data)

        responses.add(
            responses.POST,
            "http://localhost:8420/voices",
            json=mock_voice_response,
            status=200,
        )

        result = client.create_voice(
            name="test_voice", audio=audio_file, audio_filename="test.mp3"
        )

        assert isinstance(result, VoiceResponse)
        assert result.id == "test_voice"

    def test_create_voice_missing_filename(self, client, sample_audio_data):
        """Test error when filename is missing for file object."""
        audio_file = io.BytesIO(sample_audio_data)

        with pytest.raises(TTSValidationError) as exc_info:
            client.create_voice(name="test_voice", audio=audio_file)
        assert "audio_filename is required" in str(exc_info.value)

    def test_create_voice_file_not_found(self, client):
        """Test error when audio file doesn't exist."""
        with pytest.raises(TTSValidationError) as exc_info:
            client.create_voice(name="test_voice", audio="/nonexistent/file.mp3")
        assert "Audio file not found" in str(exc_info.value)

    @responses.activate
    def test_delete_voice_success(self, client):
        """Test successful voice deletion."""
        responses.add(
            responses.DELETE,
            "http://localhost:8420/voices/test_voice",
            json={"message": "Voice 'test_voice' deleted successfully"},
            status=200,
        )

        result = client.delete_voice("test_voice")
        assert "deleted successfully" in result["message"]

    @responses.activate
    def test_delete_voice_not_found(self, client):
        """Test deleting non-existent voice."""
        responses.add(
            responses.DELETE,
            "http://localhost:8420/voices/nonexistent",
            json={"detail": "Voice 'nonexistent' not found"},
            status=404,
        )

        with pytest.raises(TTSNotFoundError):
            client.delete_voice("nonexistent")

    @responses.activate
    def test_generate_speech_success(self, client, sample_audio_data):
        """Test successful speech generation."""
        responses.add(
            responses.POST,
            "http://localhost:8420/tts",
            body=sample_audio_data,
            status=200,
            headers={"Content-Type": "audio/mpeg"},
        )

        result = client.generate_speech(text="Hello world", voice_id="test_voice")

        assert result == sample_audio_data

        # Check request was made with correct data
        request = responses.calls[0].request
        request_data = json.loads(request.body)
        assert request_data["text"] == "Hello world"
        assert request_data["voice_id"] == "test_voice"
        assert request_data["temperature"] == 0.7  # Default value

    @responses.activate
    def test_generate_speech_with_custom_params(self, client, sample_audio_data):
        """Test speech generation with custom parameters."""
        responses.add(
            responses.POST,
            "http://localhost:8420/tts",
            body=sample_audio_data,
            status=200,
        )

        result = client.generate_speech(
            text="Hello world",
            voice_id="test_voice",
            temperature=0.9,
            top_p=0.8,
            seed=42,
        )

        assert result == sample_audio_data

        # Check custom parameters were sent
        request = responses.calls[0].request
        request_data = json.loads(request.body)
        assert request_data["temperature"] == 0.9
        assert request_data["top_p"] == 0.8
        assert request_data["seed"] == 42

    def test_generate_speech_invalid_params(self, client):
        """Test speech generation with invalid parameters."""
        with pytest.raises(TTSValidationError):
            client.generate_speech(
                text="", voice_id="test_voice"  # Empty text should fail validation
            )

        with pytest.raises(TTSValidationError):
            client.generate_speech(
                text="Hello world",
                voice_id="test_voice",
                temperature=5.0,  # Invalid temperature
            )

    @responses.activate
    def test_save_speech_to_file(self, client, sample_audio_data, tmp_path):
        """Test saving speech to file."""
        responses.add(
            responses.POST,
            "http://localhost:8420/tts",
            body=sample_audio_data,
            status=200,
        )

        output_file = tmp_path / "output.mp3"
        result_path = client.save_speech_to_file(
            text="Hello world", voice_id="test_voice", output_path=output_file
        )

        assert result_path == output_file
        assert output_file.exists()
        assert output_file.read_bytes() == sample_audio_data

    @responses.activate
    def test_server_error_handling(self, client):
        """Test handling of server errors."""
        responses.add(
            responses.GET,
            "http://localhost:8420/voices",
            json={"detail": "Internal server error"},
            status=500,
        )

        with pytest.raises(TTSServerError) as exc_info:
            client.list_voices()
        assert exc_info.value.status_code == 500

    @responses.activate
    def test_validation_error_handling(self, client):
        """Test handling of validation errors."""
        responses.add(
            responses.POST,
            "http://localhost:8420/voices",
            json={"detail": "Invalid audio format"},
            status=400,
        )

        with pytest.raises(TTSValidationError) as exc_info:
            client.create_voice(
                name="test", audio=io.BytesIO(b"data"), audio_filename="test.mp3"
            )
        assert exc_info.value.status_code == 400

    def test_connection_error_handling(self, client):
        """Test handling of connection errors."""
        with patch.object(
            client.session, "request", side_effect=ConnectionError("Connection failed")
        ):
            with pytest.raises(TTSConnectionError) as exc_info:
                client.health()
            assert "Failed to connect to server" in str(exc_info.value)

    def test_timeout_error_handling(self, client):
        """Test handling of timeout errors."""
        with patch.object(
            client.session, "request", side_effect=Timeout("Request timed out")
        ):
            with pytest.raises(TTSConnectionError) as exc_info:
                client.health()
            assert "Request timeout" in str(exc_info.value)

    def test_context_manager(self, client):
        """Test client as context manager."""
        with patch.object(client.session, "close") as mock_close:
            with client:
                pass
            mock_close.assert_called_once()


class TestIntegrationScenarios:
    """Integration test scenarios."""

    @responses.activate
    def test_full_workflow(
        self,
        client,
        mock_voice_response,
        mock_tts_response,
        sample_audio_data,
        arnold_transcript,
        tmp_path,
    ):
        """Test complete workflow: create voice, generate speech, delete voice."""
        # Create temporary audio file
        audio_file = tmp_path / "sample.mp3"
        audio_file.write_bytes(sample_audio_data)

        # Mock all endpoints
        responses.add(
            responses.POST,
            "http://localhost:8420/voices",
            json=mock_voice_response,
            status=200,
        )
        responses.add(
            responses.POST,
            "http://localhost:8420/tts",
            body=sample_audio_data,
            status=200,
        )
        responses.add(
            responses.DELETE,
            "http://localhost:8420/voices/test_voice",
            json={"message": "Voice deleted"},
            status=200,
        )

        # 1. Create voice
        voice = client.create_voice(
            name="test_voice", audio=str(audio_file), transcript=arnold_transcript
        )
        assert voice.id == "test_voice"

        # 2. Generate speech
        audio_data = client.generate_speech(
            text="Hello from test voice!", voice_id="test_voice"
        )
        assert audio_data == sample_audio_data

        # 3. Delete voice
        result = client.delete_voice("test_voice")
        assert "deleted" in result["message"]

    @responses.activate
    def test_error_recovery(self, client):
        """Test error recovery scenarios."""
        # First request fails, second succeeds
        responses.add(
            responses.GET,
            "http://localhost:8420/health",
            json={"detail": "Server error"},
            status=500,
        )
        responses.add(
            responses.GET,
            "http://localhost:8420/health",
            json={"status": "ok"},
            status=200,
        )

        # First request should fail
        with pytest.raises(TTSServerError):
            client.health()

        # Second request should succeed
        result = client.health()
        assert result["status"] == "ok"


# Test configuration
@pytest.fixture(scope="session")
def pytest_configure():
    """Configure pytest."""
    pytest.register_assert_rewrite("plomtts")
