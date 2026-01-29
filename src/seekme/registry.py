"""Registry for SDK extension points."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from .db import Database
from .embeddings import Embedder
from .errors import ExtensionNotFoundError
from .vector import VectorStore

DatabaseFactory = Callable[..., Database]
VectorStoreFactory = Callable[..., VectorStore]
EmbedderFactory = Callable[..., Embedder]

DEFAULT_DB_DRIVER = "sql"
DEFAULT_VECTOR_STORE = "sql"
DEFAULT_EMBEDDER = "llm"

_db_factories: dict[str, DatabaseFactory] = {}
_vector_factories: dict[str, VectorStoreFactory] = {}
_embedder_factories: dict[str, EmbedderFactory] = {}
_defaults_loaded = False


def register_db_driver(name: str, factory: DatabaseFactory) -> None:
    """Register a database driver factory."""

    _db_factories[_normalize_name(name)] = factory


def register_vector_store(name: str, factory: VectorStoreFactory) -> None:
    """Register a vector store factory."""

    _vector_factories[_normalize_name(name)] = factory


def register_embedder(name: str, factory: EmbedderFactory) -> None:
    """Register an embedder factory."""

    _embedder_factories[_normalize_name(name)] = factory


def get_db_driver(name: str) -> DatabaseFactory:
    """Return the database driver factory for the given name."""

    key = _normalize_name(name)
    try:
        return _db_factories[key]
    except KeyError as exc:  # pragma: no cover - exercised via error path tests
        raise ExtensionNotFoundError(f"Database driver '{name}' is not registered.") from exc


def get_vector_store(name: str) -> VectorStoreFactory:
    """Return the vector store factory for the given name."""

    key = _normalize_name(name)
    try:
        return _vector_factories[key]
    except KeyError as exc:  # pragma: no cover - exercised via error path tests
        raise ExtensionNotFoundError(f"Vector store '{name}' is not registered.") from exc


def get_embedder(name: str) -> EmbedderFactory:
    """Return the embedder factory for the given name."""

    key = _normalize_name(name)
    try:
        return _embedder_factories[key]
    except KeyError as exc:  # pragma: no cover - exercised via error path tests
        raise ExtensionNotFoundError(f"Embedder '{name}' is not registered.") from exc


def list_db_drivers() -> Iterable[str]:
    """List registered database driver names."""

    return sorted(_db_factories)


def list_vector_stores() -> Iterable[str]:
    """List registered vector store names."""

    return sorted(_vector_factories)


def list_embedders() -> Iterable[str]:
    """List registered embedder names."""

    return sorted(_embedder_factories)


def ensure_defaults() -> None:
    """Load default implementations into the registry."""

    global _defaults_loaded
    if _defaults_loaded:
        return
    from ._defaults import register_defaults

    register_defaults()
    _defaults_loaded = True


def _normalize_name(name: str) -> str:
    value = name.strip().lower()
    if not value:
        raise ValueError("Extension name must be non-empty.")
    return value
