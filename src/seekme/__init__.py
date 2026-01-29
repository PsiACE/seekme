"""SeekMe SDK package."""

from .client import Client
from .errors import (
    ConfigurationError,
    DatabaseConnectionError,
    EmbeddingNotConfiguredError,
    EmbeddingResponseError,
    ExtensionNotFoundError,
    InvalidExtensionNameError,
    InvalidIdentifierError,
    OptionalDependencyError,
    QueryError,
    QueryExecutionError,
    QueryFetchError,
    SeekMeError,
    TransactionError,
    ValidationError,
)

__all__ = [
    "Client",
    "ConfigurationError",
    "DatabaseConnectionError",
    "EmbeddingNotConfiguredError",
    "EmbeddingResponseError",
    "ExtensionNotFoundError",
    "InvalidExtensionNameError",
    "InvalidIdentifierError",
    "OptionalDependencyError",
    "QueryError",
    "QueryExecutionError",
    "QueryFetchError",
    "SeekMeError",
    "TransactionError",
    "ValidationError",
]
