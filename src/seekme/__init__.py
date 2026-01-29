"""SeekMe SDK package."""

from .client import Client
from .exceptions import ConfigurationError, DatabaseError, EmbeddingError, SeekMeError, ValidationError

__all__ = [
    "Client",
    "ConfigurationError",
    "DatabaseError",
    "EmbeddingError",
    "SeekMeError",
    "ValidationError",
]
