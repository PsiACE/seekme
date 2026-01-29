"""SQL-backed vector store implementation."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .core import VectorStore
from ..db import Database
from ..embeddings import Embedder
from ..errors import ConfigurationError
from ..types import Document, Ids, Vector, VectorQuery, Vectors

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SQLVectorStore(VectorStore):
    """Vector store implemented with SQL execution."""

    def __init__(self, db: Database, *, embedder: Embedder | None = None) -> None:
        self._db = db
        self._embedder = embedder

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
        query: VectorQuery,
        top_k: int,
        *,
        where: Mapping[str, Any] | None = None,
        return_fields: Sequence[str] | None = None,
        include_distance: bool = True,
        include_metadata: bool = True,
    ) -> list[Mapping[str, Any]]:
        _validate_identifier(collection)
        if where:
            raise NotImplementedError("where filtering is not implemented yet.")
        if top_k <= 0:
            return []
        vector = self._resolve_query(query)
        select_fields = _select_fields(return_fields, include_metadata)
        distance_expr = "l2_distance(embedding, :query)"
        select_items = list(select_fields)
        if include_distance:
            select_items.append(f"{distance_expr} AS _distance")
            order_by = "_distance"
        else:
            order_by = distance_expr
        select_clause = ", ".join(select_items)
        return self._db.fetch_all(
            f"""
            SELECT {select_clause}
            FROM {collection}
            ORDER BY {order_by} ASC
            LIMIT :top_k
            """,
            {"query": _vector_literal(vector), "top_k": top_k},
        )

    def _resolve_query(self, query: VectorQuery) -> Vector:
        if isinstance(query, str):
            return self._embed_text(query)
        return query

    def _embed_text(self, query: Document) -> Vector:
        if self._embedder is None:
            raise ConfigurationError(
                "Embedding is not configured. Provide an embedder or install extras: pip install 'seekme[embeddings]'"
            )
        embeddings = self._embedder.embed([query])
        if not embeddings:
            raise ValueError("Embedding result is empty.")
        return embeddings[0]


def _vector_literal(vector: Vector) -> str:
    return json.dumps([float(x) for x in vector], separators=(",", ":"))


def _validate_identifier(name: str) -> None:
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"Invalid identifier: {name}")


def _select_fields(return_fields: Sequence[str] | None, include_metadata: bool) -> list[str]:
    if return_fields is None:
        fields = ["id"]
        if include_metadata:
            fields.append("metadata")
        return fields
    fields = []
    seen: set[str] = set()
    for field in return_fields:
        _validate_identifier(field)
        if field in seen:
            continue
        fields.append(field)
        seen.add(field)
    if not fields:
        raise ValueError("return_fields must include at least one column.")
    return fields


__all__ = ["SQLVectorStore"]
