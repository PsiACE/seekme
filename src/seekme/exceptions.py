"""SDK exception definitions."""

from __future__ import annotations


class SeekMeError(Exception):
    """Base error for the SDK."""


class ConfigurationError(SeekMeError):
    """Raised when configuration is invalid or incomplete."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Configuration is invalid or incomplete.")

    @classmethod
    def extension_not_found(cls, kind: str, name: str) -> ConfigurationError:
        return cls(f"{kind} '{name}' is not registered.")

    @classmethod
    def database_driver_not_found(cls, name: str) -> ConfigurationError:
        return cls(f"Database driver '{name}' is not registered.")

    @classmethod
    def vector_store_not_found(cls, name: str) -> ConfigurationError:
        return cls(f"Vector store '{name}' is not registered.")

    @classmethod
    def embedder_not_found(cls, name: str) -> ConfigurationError:
        return cls(f"Embedder '{name}' is not registered.")

    @classmethod
    def invalid_extension_name(cls) -> ConfigurationError:
        return cls("Extension name must be non-empty.")

    @classmethod
    def embedding_not_configured(cls) -> ConfigurationError:
        return cls(
            "Embedding is not configured. Provide an embedder or install extras: "
            "pip install 'seekme[remote-embeddings]' or 'seekme[local-embeddings]'"
        )

    @classmethod
    def missing_optional_dependency(cls, extra: str) -> ConfigurationError:
        return cls(f"{extra} support requires extras: pip install 'seekme[{extra}]'")


class DatabaseError(SeekMeError):
    """Raised when database operations fail."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Database operation failed.")

    @classmethod
    def connection_failed(cls) -> DatabaseError:
        return cls("Database connection failed.")

    @classmethod
    def execution_failed(cls) -> DatabaseError:
        return cls("SQL execution failed.")

    @classmethod
    def fetch_failed(cls) -> DatabaseError:
        return cls("SQL fetch failed.")

    @classmethod
    def transaction_failed(cls, action: str) -> DatabaseError:
        return cls(f"Transaction {action} failed.")


class EmbeddingError(SeekMeError):
    """Raised when embedding operations fail."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Embedding operation failed.")

    @classmethod
    def request_failed(cls) -> EmbeddingError:
        return cls("Embedding request failed.")

    @classmethod
    def response_failed(cls) -> EmbeddingError:
        return cls("Embedding response parsing failed.")


class ValidationError(ValueError, SeekMeError):
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

    @classmethod
    def invalid_identifier(cls, name: str) -> ValidationError:
        return cls(f"Invalid identifier: {name}")

    @classmethod
    def embedding_response_unsupported(cls) -> ValidationError:
        return cls("Unsupported embedding response format.")

    @classmethod
    def embedding_missing(cls) -> ValidationError:
        return cls("Embedding item missing embedding field.")

    @classmethod
    def invalid_filter_value(cls, name: str) -> ValidationError:
        return cls(f"Invalid filter value for '{name}'.")

    @classmethod
    def invalid_filter_key(cls, name: str) -> ValidationError:
        return cls(f"Invalid filter key: {name}")

    @classmethod
    def metadata_serialization_failed(cls) -> ValidationError:
        return cls("Metadata must be JSON serializable.")

    @classmethod
    def invalid_seekdb_url(cls, url: str) -> ValidationError:
        return cls(f"Invalid seekdb URL: {url}")

    @classmethod
    def seekdb_path_not_directory(cls, path: str) -> ValidationError:
        return cls(f"Seekdb path is not a directory: {path}")

    @classmethod
    def seekdb_already_opened(cls, path: str) -> ValidationError:
        return cls(f"Seekdb already opened at: {path}")

    @classmethod
    def unsupported_seekdb_options(cls, options: list[str]) -> ValidationError:
        return cls(f"Unsupported seekdb options: {options}")

    @classmethod
    def missing_sql_parameter(cls, name: str) -> ValidationError:
        return cls(f"Missing SQL parameter: {name}")

    @classmethod
    def invalid_index_option(cls, name: str, value: object) -> ValidationError:
        return cls(f"Invalid index option '{name}': {value}")

    @classmethod
    def invalid_index_property_name(cls, name: str) -> ValidationError:
        return cls(f"Invalid index property name: {name}")

    @classmethod
    def invalid_index_property_value(cls, name: str) -> ValidationError:
        return cls(f"Invalid index property value for '{name}'.")

    @classmethod
    def unsupported_index_option(cls, name: str, value: object) -> ValidationError:
        return cls(f"Unsupported index option '{name}': {value}")

    @classmethod
    def distance_required(cls) -> ValidationError:
        return cls("Distance must be provided for vector search.")

    @classmethod
    def unsupported_index_property(cls, index_type: object, name: object) -> ValidationError:
        return cls(f"Index type '{index_type}' does not support property '{name}'.")

    @classmethod
    def missing_index_property(cls, index_type: object, name: str) -> ValidationError:
        return cls(f"Index type '{index_type}' requires property '{name}'.")


__all__ = [
    "ConfigurationError",
    "DatabaseError",
    "EmbeddingError",
    "SeekMeError",
    "ValidationError",
]
