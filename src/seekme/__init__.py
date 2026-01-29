"""SeekMe SDK package."""

from .client import Client
from .errors import ConfigurationError, DatabaseConnectionError, QueryError, SeekMeError

__all__ = [
    "Client",
    "ConfigurationError",
    "DatabaseConnectionError",
    "QueryError",
    "SeekMeError",
]
