"""Unit tests for vector SQL helpers."""

from __future__ import annotations

import pytest

from seekme.exceptions import ValidationError
from seekme.vector import VectorIndexConfig, sql as vector_sql


def test_create_collection_sql_omits_vector_index_by_default() -> None:
    sql = vector_sql._create_collection_sql("seekme_vectors", 3)

    assert "VECTOR(3)" in sql
    assert "VECTOR INDEX idx_vec (embedding)" not in sql


def test_resolve_distance_uses_index_distance() -> None:
    name, func = vector_sql._resolve_distance("l2")

    assert name == "l2"
    assert func == "l2_distance"


def test_resolve_distance_rejects_invalid() -> None:
    with pytest.raises(ValidationError, match="Invalid index option"):
        vector_sql._resolve_distance("bad-distance")


def test_resolve_distance_requires_value() -> None:
    with pytest.raises(ValidationError, match="Distance must be provided"):
        vector_sql._resolve_distance(None)


def test_create_vector_index_sql() -> None:
    index = VectorIndexConfig(name="idx_vec", distance="l2", index_type="hnsw", lib="vsag")
    sql = index.render_create_sql("seekme_vectors")

    assert "CREATE VECTOR INDEX idx_vec ON seekme_vectors (embedding)" in sql
    assert "DISTANCE=l2" in sql


def test_ivf_pq_requires_m() -> None:
    with pytest.raises(ValidationError, match="requires property 'm'"):
        VectorIndexConfig(
            name="idx_vec",
            distance="l2",
            index_type="ivf_pq",
            lib="vsag",
        )


def test_ivf_flat_rejects_unknown_property() -> None:
    with pytest.raises(ValidationError, match="does not support property"):
        VectorIndexConfig(
            name="idx_vec",
            distance="l2",
            index_type="ivf_flat",
            lib="vsag",
            properties={"m": 4},
        )


def test_index_type_requires_lowercase() -> None:
    with pytest.raises(ValidationError, match="Invalid index option"):
        VectorIndexConfig(
            name="idx_vec",
            distance="l2",
            index_type="HNSW",
            lib="vsag",
        )
