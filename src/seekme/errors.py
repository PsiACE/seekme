"""SDK error definitions."""

from __future__ import annotations


class SeekMeError(Exception):
    """Base error for the SDK."""


class ConfigurationError(SeekMeError):
    """Raised when configuration is invalid or incomplete."""


class DatabaseConnectionError(SeekMeError):
    """Raised when the client cannot connect to the database."""


class QueryError(SeekMeError):
    """Raised when a query execution fails."""


class ExtensionNotFoundError(SeekMeError):
    """Raised when a requested extension is not registered."""


__all__ = [
    "ConfigurationError",
    "DatabaseConnectionError",
    "ExtensionNotFoundError",
    "QueryError",
    "SeekMeError",
]
