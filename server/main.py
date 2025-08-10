"""Main FastAPI application for plomtts."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import tts, voices
from core.config import settings
from core.fish_client import FishSpeechClient
from core.voice_manager import VoiceManager

# Create FastAPI app
app = FastAPI(
    title="plomtts",
    description="🎤 High-performance AI Text-to-Speech server powered by fish-speech",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware to allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(voices.router)
app.include_router(tts.router)

# Initialize components
fish_client = FishSpeechClient()
voice_manager = VoiceManager()


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with basic info."""
    return {
        "name": "plomtts",
        "description": "🎤 AI Text-to-Speech server powered by fish-speech",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print("🚀 Starting plomtts server...")
    print(f"📁 Voices directory: {settings.VOICES_DIR}")
    print(f"🐟 Fish-speech endpoint: {settings.fish_speech_url}")

    # Ensure voices directory exists
    settings.VOICES_DIR.mkdir(parents=True, exist_ok=True)

    # Log available voices
    voices = voice_manager.list_voices()
    print(f"🎵 Found {len(voices)} voices: {[v.name for v in voices]}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "plomtts.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
