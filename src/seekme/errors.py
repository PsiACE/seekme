"""SDK error definitions."""

from __future__ import annotations


class SeekMeError(Exception):
    """Base error for the SDK."""


class ConfigurationError(SeekMeError):
    """Raised when configuration is invalid or incomplete."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Configuration is invalid or incomplete.")


class DatabaseConnectionError(SeekMeError):
    """Raised when the client cannot connect to the database."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Database connection failed.")


class QueryError(SeekMeError):
    """Raised when a query execution fails."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Database operation failed.")


class QueryExecutionError(QueryError):
    """Raised when executing a SQL statement fails."""

    def __init__(self) -> None:
        super().__init__("SQL execution failed.")


class QueryFetchError(QueryError):
    """Raised when fetching query results fails."""

    def __init__(self) -> None:
        super().__init__("SQL fetch failed.")


class TransactionError(QueryError):
    """Raised when a transaction operation fails."""

    def __init__(self, action: str) -> None:
        super().__init__(f"Transaction {action} failed.")


class ExtensionNotFoundError(SeekMeError):
    """Raised when a requested extension is not registered."""

    def __init__(self, kind: str, name: str) -> None:
        super().__init__(f"{kind} '{name}' is not registered.")

    @classmethod
    def database_driver(cls, name: str) -> ExtensionNotFoundError:
        return cls("Database driver", name)

    @classmethod
    def vector_store(cls, name: str) -> ExtensionNotFoundError:
        return cls("Vector store", name)

    @classmethod
    def embedder(cls, name: str) -> ExtensionNotFoundError:
        return cls("Embedder", name)


class InvalidExtensionNameError(ValueError):
    """Raised when an extension name is invalid."""

    def __init__(self) -> None:
        super().__init__("Extension name must be non-empty.")


class InvalidIdentifierError(ValueError):
    """Raised when an identifier is invalid."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Invalid identifier: {name}")


class ValidationError(ValueError):
    """Raised when user input fails validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @classmethod
    def dimension_must_be_positive(cls) -> ValidationError:
        return cls("Dimension must be positive.")

    @classmethod
    def ids_vectors_mismatch(cls) -> ValidationError:
        return cls("Ids and vectors length mismatch.")

    @classmethod
    def metadatas_mismatch(cls) -> ValidationError:
        return cls("Metadatas length mismatch.")

    @classmethod
    def return_fields_empty(cls) -> ValidationError:
        return cls("Return fields must include at least one column.")

    @classmethod
    def embedding_empty(cls) -> ValidationError:
        return cls("Embedding result is empty.")


class EmbeddingNotConfiguredError(ConfigurationError):
    """Raised when embeddings are required but not configured."""

    def __init__(self) -> None:
        super().__init__(
            "Embedding is not configured. Provide an embedder or install extras: pip install 'seekme[embeddings]'"
        )


class OptionalDependencyError(ImportError):
    """Raised when an optional dependency is missing."""

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @classmethod
    def embeddings(cls) -> OptionalDependencyError:
        return cls("Embedding support requires extras: pip install 'seekme[embeddings]'")


class EmbeddingResponseError(TypeError):
    """Raised when the embedding provider returns an unexpected response."""

    def __init__(self, message: str) -> None:
        super().__init__(message)

    @classmethod
    def unsupported_format(cls) -> EmbeddingResponseError:
        return cls("Unsupported embedding response format.")

    @classmethod
    def missing_embedding(cls) -> EmbeddingResponseError:
        return cls("Embedding item missing embedding field.")


__all__ = [
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
