# 🎤 plomtts

A high-performance AI Text-to-Speech server powered by [fish-speech](https://github.com/fishaudio/fish-speech), designed for seamless integration across multiple projects.

## 🚀 Features

### 🎵 Voice Management
- **Voice Creation**: Upload `.mp3` sample files with `.txt` transcripts
- **Voice Library**: Add, remove, and list custom voices via REST API
- **Quality Control**: Automatic validation of audio samples and transcripts
- **Voice Cloning**: Generate speech using your custom voice models

### 🌐 REST API
- **OpenAPI/Swagger**: Auto-generated documentation and client SDKs
- **RESTful Endpoints**: Standard HTTP methods for all operations
- **JSON Responses**: Consistent API response format
- **Error Handling**: Detailed error messages and status codes

## 🔧 Quick Start

### Prerequisites
- Docker and Docker Compose
- NVIDIA GPU with CUDA support (recommended: RTX 3090+)
- Python 3.12+ (for client development)

### Run with Docker

1. **Start with Docker**
   ```bash
   docker run \
     -p 8420:8420 \
     -v ./models:/app/models \
     -v ./voices:/app/voices \
     -e CUDA_VISIBLE_DEVICES=0 \
     avalonlee/plomtts:latest
   ```

3. **Verify installation**
   ```bash
   curl http://localhost:8420/health
   ```

## 📚 API Documentation

Once running, visit `http://localhost:8420/docs` for interactive API documentation.

### Core Endpoints

#### Voice Management
- `GET /voices` - List all available voices
- `POST /voices` - Upload a new voice (MP3 + optional transcript)
- `DELETE /voices/{voice_id}` - Remove a voice
- `GET /voices/{voice_id}` - Get voice details

#### Text-to-Speech
- `POST /tts` - Generate speech from text (instant response)
- `POST /tts/stream` - Stream audio generation

### Example Usage

```bash
# Upload a new voice with transcript
curl -X POST "http://localhost:8420/voices" \
  -F "audio=@sample.mp3" \
  -F "transcript=$(cat transcript.txt)" \
  -F "name=my_voice"

# Generate TTS
curl -X POST "http://localhost:8420/tts" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world!", "voice_id": "my_voice"}' \
  --output output.mp3
```

## 🐍 Python Client

The Python client is available on PyPI as `plomtts-client`.

### Installation
```bash
pip install plomtts-client
```

### Usage
```python
from plomtts import TTSClient

client = TTSClient("http://localhost:8420")

# Upload a voice with transcript
with open("sample.mp3", "rb") as audio, open("transcript.txt", "r") as transcript:
    voice = client.create_voice(
        name="my_voice",
        audio=audio,
        transcript=transcript.read()
    )

# Upload a voice without transcript (auto-generated)
with open("sample.mp3", "rb") as audio:
    voice = client.create_voice(
        name="my_voice",
        audio=audio
    )

# Generate speech
audio_bytes = client.generate_speech(
    text="Hello, this is AI-generated speech!",
    voice_id=voice.id
)

# Save audio
with open("output.mp3", "wb") as f:
    f.write(audio_bytes)
```

## 🐳 Docker Configuration

### Environment Variables
- `PLOMTTS_PORT`: Server port (default: 8420)
- `PLOMTTS_HOST`: Server host (default: 0.0.0.0)
- `CUDA_VISIBLE_DEVICES`: GPU devices to use

### Docker Run Example
```bash
docker run -d \
  -p 8420:8420 \
  -v ./voices:/app/voices \
  -e PLOMTTS_PORT=8420 \
  -e PLOMTTS_HOST=0.0.0.0 \
  -e CUDA_VISIBLE_DEVICES=0 \
  avalonlee/plomtts:latest
```

## 🔗 Integration Projects

plomtts is designed to power TTS functionality across multiple projects:

- **[discord-bots](https://github.com/plomdawg/discord-bots)**: Discord TTS voicebot integration
- **[plomtts-hass](https://github.com/plomdawg/plomtts-hass)**: Home Assistant TTS client  
- **[plomtts-twitch](https://github.com/plomdawg/plomtts-twitch)**: Twitch stream TTS integration

