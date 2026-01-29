"""Integration tests for vector store behaviors."""

from __future__ import annotations

import pytest

from seekme import Client
from seekme.exceptions import ConfigurationError


def test_vector_store_search_fields(client: Client, table_cleanup: list[str]) -> None:
    store = client.vector_store
    assert store is not None
    store.create_collection("seekme_vectors", dimension=3)
    table_cleanup.append("seekme_vectors")

    store.upsert(
        "seekme_vectors",
        ids=["v1", "v2"],
        vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        metadatas=[{"lang": "en"}, {"lang": "zh"}],
    )

    results = store.search("seekme_vectors", query=[1.0, 0.0, 0.0], top_k=1)
    assert results
    assert "_distance" in results[0]
    assert "metadata" in results[0]
    assert results[0]["id"] == "v1"

    results = store.search(
        "seekme_vectors",
        query=[1.0, 0.0, 0.0],
        top_k=1,
        return_fields=["id"],
        include_distance=False,
    )
    assert results == [{"id": "v1"}]


def test_vector_store_requires_embedder_for_text_query(client: Client, table_cleanup: list[str]) -> None:
    store = client.vector_store
    assert store is not None
    store.create_collection("seekme_vectors_text", dimension=3)
    table_cleanup.append("seekme_vectors_text")

    with pytest.raises(ConfigurationError):
        store.search("seekme_vectors_text", query="hello", top_k=1)
