"""PlomTTS Python Client - AI Text-to-Speech client library."""

from .client import TTSClient
from .exceptions import (
    TTSConnectionError,
    TTSError,
    TTSNotFoundError,
    TTSServerError,
    TTSValidationError,
)
from .models import (
    HealthResponse,
    TTSRequest,
    TTSResponse,
    VoiceListResponse,
    VoiceResponse,
)

__version__ = "0.1.0"
__all__ = [
    "TTSClient",
    "TTSError",
    "TTSConnectionError",
    "TTSNotFoundError",
    "TTSValidationError",
    "TTSServerError",
    "TTSRequest",
    "TTSResponse",
    "HealthResponse",
    "VoiceResponse",
    "VoiceListResponse",
]
