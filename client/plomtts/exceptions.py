"""Custom exceptions for TTS client."""

from typing import Optional


class TTSError(Exception):
    """Base exception for TTS client errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TTSConnectionError(TTSError):
    """Raised when connection to TTS server fails."""

    pass


class TTSNotFoundError(TTSError):
    """Raised when a resource is not found (404)."""

    pass


class TTSValidationError(TTSError):
    """Raised when request validation fails (400)."""

    pass


class TTSServerError(TTSError):
    """Raised when server returns 5xx error."""

    pass
