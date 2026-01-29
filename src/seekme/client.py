"""Unified SDK client entrypoint."""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine

from .db import Database
from .embeddings import Embedder
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
    def from_database_url(cls, url: str, **engine_kwargs: Any) -> "Client":
        """Create a client from a SQLAlchemy database URL."""

        engine = create_engine(url, **engine_kwargs)
        from .db.drivers import SQLAlchemyDatabase

        return cls(db=SQLAlchemyDatabase(engine))

    @property
    def db(self) -> Database | None:
        """Return the database component."""

        return self._db

    @property
    def vector_store(self) -> VectorStore | None:
        """Return the vector store component."""

        return self._vector_store

    @property
    def embedder(self) -> Embedder | None:
        """Return the embedding component."""

        return self._embedder

    def connect(self) -> "Client":
        """Explicitly connect underlying components when supported."""

        if self._db is not None:
            self._db.connect()
        return self

    def close(self) -> None:
        """Close underlying components when supported."""

        if self._db is not None:
            self._db.close()

    def __enter__(self) -> "Client":
        return self.connect()

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any) -> None:
        self.close()


__all__ = ["Client"]
