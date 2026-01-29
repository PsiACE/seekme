"""SeekMe SDK package."""

from .client import Client
from .errors import (
    ConfigurationError,
    DatabaseConnectionError,
    ExtensionNotFoundError,
    QueryError,
    SeekMeError,
)

__all__ = [
    "Client",
    "ConfigurationError",
    "DatabaseConnectionError",
    "ExtensionNotFoundError",
    "QueryError",
    "SeekMeError",
]
