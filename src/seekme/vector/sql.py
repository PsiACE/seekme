"""SQL-backed vector store implementation."""

# ruff: noqa: S608

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

from ..db import Database
from ..embeddings import Embedder
from ..exceptions import ConfigurationError, ValidationError
from ..types import Document, Ids, Vector, VectorQuery, Vectors
from .core import VectorStore

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SQLVectorStore(VectorStore):
    """Vector store implemented with SQL execution."""

    def __init__(self, db: Database, *, embedder: Embedder | None = None) -> None:
        self._db = db
        self._embedder = embedder

    def create_collection(self, name: str, dimension: int) -> None:
        _validate_identifier(name)
        if dimension <= 0:
            raise ValidationError.dimension_must_be_positive()
        self._db.execute(
            f"""  # noqa: S608
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
            raise ValidationError.ids_vectors_mismatch()
        if metadatas is not None and len(metadatas) != len(ids_list):
            raise ValidationError.metadatas_mismatch()
        for position, (idx, vector) in enumerate(zip(ids_list, vectors_list)):
            metadata = None
            if metadatas is not None:
                metadata = _dump_metadata(metadatas[position])
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
        where_clause, where_params = _build_where_clause(where)
        return self._db.fetch_all(
            f"""
            SELECT {select_clause}
            FROM {collection}
            {where_clause}
            ORDER BY {order_by} ASC
            LIMIT :top_k
            """,
            {"query": _vector_literal(vector), "top_k": top_k, **where_params},
        )

    def _resolve_query(self, query: VectorQuery) -> Vector:
        if isinstance(query, str):
            return self._embed_text(query)
        return query

    def _embed_text(self, query: Document) -> Vector:
        if self._embedder is None:
            raise ConfigurationError.embedding_not_configured()
        embeddings = self._embedder.embed([query])
        if not embeddings:
            raise ValidationError.embedding_empty()
        return embeddings[0]


def _vector_literal(vector: Vector) -> str:
    return json.dumps([float(x) for x in vector], separators=(",", ":"))


def _validate_identifier(name: str) -> None:
    if not _IDENTIFIER_RE.match(name):
        raise ValidationError.invalid_identifier(name)


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
        raise ValidationError.return_fields_empty()
    return fields


def _build_where_clause(where: Mapping[str, Any] | None) -> tuple[str, dict[str, Any]]:
    if not where:
        return "", {}
    clauses: list[str] = []
    params: dict[str, Any] = {}
    for index, (key, value) in enumerate(where.items()):
        param_name = f"w{index}"
        if key == "id":
            clauses.append(f"id = :{param_name}")
            params[param_name] = value
            continue
        key_name = _normalize_filter_key(key)
        path_param = f"p{index}"
        params[path_param] = _json_path(key_name)
        if value is None:
            clauses.append(f"JSON_EXTRACT(metadata, :{path_param}) IS NULL")
            continue
        params[param_name] = _json_filter_value(key_name, value)
        clauses.append(f"JSON_EXTRACT(metadata, :{path_param}) = CAST(:{param_name} AS JSON)")
    return "WHERE " + " AND ".join(clauses), params


def _normalize_filter_key(key: Any) -> str:
    if not isinstance(key, str) or not key:
        raise ValidationError.invalid_filter_key(str(key))
    return key


def _json_path(key: str) -> str:
    return "$." + json.dumps(key)


def _json_filter_value(name: str, value: Any) -> str:
    try:
        return json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError.invalid_filter_value(name) from exc


def _dump_metadata(value: Any) -> str:
    try:
        return json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError.metadata_serialization_failed() from exc


__all__ = ["SQLVectorStore"]
