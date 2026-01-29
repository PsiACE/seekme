"""SQLAlchemy-backed vector store implementation."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .core import VectorStore
from ..db import Database
from ..types import Ids, Vector, Vectors

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SQLAlchemyVectorStore(VectorStore):
    """Vector store implemented with SQL execution."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def create_collection(self, name: str, dimension: int) -> None:
        _validate_identifier(name)
        if dimension <= 0:
            raise ValueError("dimension must be positive.")
        self._db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {name} (
                id VARCHAR(64) PRIMARY KEY,
                embedding VECTOR({dimension}) NOT NULL,
                metadata JSON
            )
            """
        )
        self._db.commit()

    def delete_collection(self, name: str) -> None:
        _validate_identifier(name)
        self._db.execute(f"DROP TABLE IF EXISTS {name}")
        self._db.commit()

    def upsert(
        self,
        collection: str,
        ids: Ids,
        vectors: Vectors,
        metadatas: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        _validate_identifier(collection)
        ids_list = list(ids)
        vectors_list = list(vectors)
        if len(ids_list) != len(vectors_list):
            raise ValueError("ids and vectors length mismatch.")
        if metadatas is not None and len(metadatas) != len(ids_list):
            raise ValueError("metadatas length mismatch.")
        for position, (idx, vector) in enumerate(zip(ids_list, vectors_list)):
            metadata = None
            if metadatas is not None:
                metadata = json.dumps(metadatas[position])
            self._db.execute(
                f"""
                INSERT INTO {collection} (id, embedding, metadata)
                VALUES (:id, :embedding, :metadata)
                ON DUPLICATE KEY UPDATE
                    embedding = VALUES(embedding),
                    metadata = VALUES(metadata)
                """,
                {
                    "id": idx,
                    "embedding": _vector_literal(vector),
                    "metadata": metadata,
                },
            )
        self._db.commit()

    def search(
        self,
        collection: str,
        query: Vector,
        top_k: int,
        where: Mapping[str, Any] | None = None,
    ) -> list[Mapping[str, Any]]:
        _validate_identifier(collection)
        if where:
            raise NotImplementedError("where filtering is not implemented yet.")
        if top_k <= 0:
            return []
        return self._db.fetch_all(
            f"""
            SELECT id, metadata, l2_distance(embedding, :query) AS distance
            FROM {collection}
            ORDER BY distance ASC
            LIMIT :top_k
            """,
            {"query": _vector_literal(query), "top_k": top_k},
        )


def _vector_literal(vector: Vector) -> str:
    return json.dumps([float(x) for x in vector], separators=(",", ":"))


def _validate_identifier(name: str) -> None:
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid identifier: {name}")


__all__ = ["SQLAlchemyVectorStore"]
