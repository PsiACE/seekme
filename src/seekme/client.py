"""Unified SDK client entrypoint."""

from __future__ import annotations

from typing import Any

from .db import Database
from .embeddings import Embedder
from .registry import DEFAULT_DB_DRIVER, DEFAULT_VECTOR_STORE, ensure_defaults, get_db_driver, get_vector_store
from .vector import VectorStore


class Client:
    """Unified client that composes DB, vector, and embedding components."""

    def __init__(
        self,
        *,
        db: Database | None = None,
        vector_store: VectorStore | None = None,
        embedder: Embedder | None = None,
    ) -> None:
        self._db = db
        self._vector_store = vector_store
        self._embedder = embedder

    @classmethod
    def from_database_url(
        cls,
        url: str,
        *,
        db_driver: str = DEFAULT_DB_DRIVER,
        **driver_kwargs: Any,
    ) -> Client:
        """Create a client from a database URL using a registered driver."""

        ensure_defaults()
        factory = get_db_driver(db_driver)
        return cls(db=factory(url, **driver_kwargs))

    @property
    def db(self) -> Database | None:
        """Return the database component."""

        return self._db

    @property
    def vector_store(self) -> VectorStore | None:
        """Return the vector store component."""

        if self._vector_store is None and self._db is not None:
            ensure_defaults()
            factory = get_vector_store(DEFAULT_VECTOR_STORE)
            self._vector_store = factory(self._db, embedder=self._embedder)
        return self._vector_store

    @property
    def embedder(self) -> Embedder | None:
        """Return the embedding component."""

        return self._embedder

    def connect(self) -> Client:
        """Explicitly connect underlying components when supported."""

        if self._db is not None:
            self._db.connect()
        return self

    def close(self) -> None:
        """Close underlying components when supported."""

        if self._db is not None:
            self._db.close()

    def __enter__(self) -> Client:
        return self.connect()

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> None:
        self.close()


__all__ = ["Client"]
