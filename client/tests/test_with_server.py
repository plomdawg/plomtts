"""Test runner script with server integration tests."""

from pathlib import Path

import pytest

from plomtts import TTSClient


@pytest.mark.live
def test_with_live_server():
    """Test client against a live PlomTTS server."""
    print("🚀 Testing PlomTTS client against live server...")

    # Check if server is running
    client = TTSClient("http://localhost:8420", timeout=10.0)

    try:
        # Test health check
        print("📡 Testing health check...")
        health = client.health()
        print(f"✅ Health check: {health}")

        # Test listing voices
        print("📋 Testing voice listing...")
        voices = client.list_voices()
        print(f"✅ Found {voices.total} voices")

        # Test creating a voice with sample audio
        print("🎤 Testing voice creation...")

        # Create a minimal MP3 file for testing
        mp3_path = Path(__file__).parent / "arnold.mp3"
        sample_audio = mp3_path.read_bytes()

        # Read Arnold transcript
        arnold_txt_path = Path(__file__).parent / "arnold.txt"
        if arnold_txt_path.exists():
            transcript = arnold_txt_path.read_text(encoding="utf-8").strip()

        try:
            voice = client.create_voice(
                name="test_client_voice",
                audio=sample_audio,
                transcript=transcript,
                audio_filename="arnold.mp3",
            )
            print(f"✅ Created voice: {voice.id}")

            # Test TTS generation
            print("🗣️ Testing TTS generation...")
            audio_data = client.generate_speech(
                text="Hello from the PlomTTS client test!",
                voice_id=voice.id,
                temperature=0.8,
            )
            print(f"✅ Generated {len(audio_data)} bytes of audio")

            # Save to file
            output_path = Path("/tmp/client_test_output.mp3")
            saved_path = client.save_speech_to_file(
                text="This is a file save test.",
                voice_id=voice.id,
                output_path=output_path,
            )
            print(f"✅ Saved audio to: {saved_path}")

            # Clean up - delete the test voice
            print("🧹 Cleaning up...")
            client.delete_voice(voice.id)
            print("✅ Test voice deleted")

        except Exception as e:
            print(f"❌ Error during voice testing: {e}")
            # Try to clean up anyway
            try:
                client.delete_voice("test_client_voice")
            except Exception:
                pass

        print("🎉 All live server tests passed!")

    except (ConnectionError, TimeoutError, ValueError) as e:
        print(f"❌ Live server test failed: {e}")
        print("💡 Make sure PlomTTS server is running on http://localhost:8420")
        pytest.fail(f"Live server test failed: {e}")
