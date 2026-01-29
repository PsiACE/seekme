"""Default registry bindings for built-in implementations."""

from __future__ import annotations

from .db.drivers.sql import SQLDatabase
from .embeddings.llm import LLMEmbedder
from .registry import (
    DEFAULT_DB_DRIVER,
    DEFAULT_EMBEDDER,
    DEFAULT_VECTOR_STORE,
    register_db_driver,
    register_embedder,
    register_vector_store,
)
from .vector.sql import SQLVectorStore


def _create_sql_database(url: str, **engine_kwargs: object) -> SQLDatabase:
    return SQLDatabase.from_url(url, **engine_kwargs)


def register_defaults() -> None:
    register_db_driver(DEFAULT_DB_DRIVER, _create_sql_database)
    register_vector_store(DEFAULT_VECTOR_STORE, SQLVectorStore)
    register_embedder(DEFAULT_EMBEDDER, LLMEmbedder)
