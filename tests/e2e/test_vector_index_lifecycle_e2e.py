"""End-to-end test for vector index lifecycle."""

from __future__ import annotations

from collections.abc import Mapping

from seekme import Client
from seekme.vector import VectorIndexConfig


def test_vector_index_lifecycle(client: Client, table_cleanup: list[str]) -> None:
    store = client.vector_store
    assert store is not None

    table_name = "seekme_vectors_index_e2e"
    index_name = "idx_vec"

    store.create_collection(table_name, dimension=3)
    table_cleanup.append(table_name)

    index = VectorIndexConfig(
        name=index_name,
        distance="l2",
        index_type="hnsw",
        lib="vsag",
    )
    store.create_vector_index(table_name, index)

    store.upsert(
        table_name,
        ids=["v1"],
        vectors=[[1.0, 0.0, 0.0]],
        metadatas=[{"tag": "e2e"}],
    )

    results = store.search(table_name, query=[1.0, 0.0, 0.0], top_k=1, distance="l2")
    assert results

    index_names = _fetch_index_names(client, table_name)
    assert index_name.lower() in index_names

    store.delete_vector_index(table_name, index_name)
    index_names = _fetch_index_names(client, table_name)
    assert index_name.lower() not in index_names


def _fetch_index_names(client: Client, table_name: str) -> set[str]:
    assert client.db is not None
    rows = client.db.fetch_all(f"SHOW INDEX FROM {table_name}")
    names: set[str] = set()
    for row in rows:
        name = _extract_index_name(row)
        if name:
            names.add(name.lower())
    return names


def _extract_index_name(row: Mapping[str, object]) -> str | None:
    for key in ("Key_name", "key_name", "Index_name", "index_name"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    return None
