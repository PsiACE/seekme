"""Integration tests for vector store behaviors."""

from __future__ import annotations

import pytest

from seekme import Client
from seekme.embeddings import LocalEmbedder
from seekme.exceptions import ConfigurationError, ValidationError


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

    results = store.search(
        "seekme_vectors",
        query=[1.0, 0.0, 0.0],
        top_k=1,
        return_fields=["id"],
        include_distance=True,
    )
    assert results
    assert results[0]["id"] == "v1"
    assert "_distance" in results[0]
    assert "metadata" not in results[0]


def test_vector_store_requires_embedder_for_text_query(client: Client, table_cleanup: list[str]) -> None:
    store = client.vector_store
    assert store is not None
    store.create_collection("seekme_vectors_text", dimension=3)
    table_cleanup.append("seekme_vectors_text")

    with pytest.raises(ConfigurationError):
        store.search("seekme_vectors_text", query="hello", top_k=1)


def test_vector_store_text_query_with_local_embedder(
    client: Client, table_cleanup: list[str], local_embedder: LocalEmbedder
) -> None:
    embedder_client = Client(db=client.db, embedder=local_embedder)
    store = embedder_client.vector_store
    assert store is not None

    sample = local_embedder.embed(["hello", "world"])
    dimension = len(sample[0])
    store.create_collection("seekme_vectors_local", dimension=dimension)
    table_cleanup.append("seekme_vectors_local")

    store.upsert(
        "seekme_vectors_local",
        ids=["v1", "v2"],
        vectors=sample,
        metadatas=[{"lang": "en"}, {"lang": "en"}],
    )

    results = store.search("seekme_vectors_local", query="hello", top_k=1, return_fields=["id"])
    assert results


def test_vector_store_where_filter_metadata(client: Client, table_cleanup: list[str]) -> None:
    store = client.vector_store
    assert store is not None
    store.create_collection("seekme_vectors_filter", dimension=3)
    table_cleanup.append("seekme_vectors_filter")

    store.upsert(
        "seekme_vectors_filter",
        ids=["v1", "v2"],
        vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        metadatas=[{"lang-code": "en"}, {"lang-code": "zh"}],
    )

    results = store.search(
        "seekme_vectors_filter",
        query=[1.0, 0.0, 0.0],
        top_k=2,
        where={"lang-code": "en"},
        return_fields=["id"],
        include_distance=False,
    )
    assert results == [{"id": "v1"}]


def test_vector_store_rejects_unserializable_metadata(client: Client, table_cleanup: list[str]) -> None:
    store = client.vector_store
    assert store is not None
    store.create_collection("seekme_vectors_invalid_meta", dimension=3)
    table_cleanup.append("seekme_vectors_invalid_meta")

    with pytest.raises(ValidationError, match="Metadata must be JSON serializable"):
        store.upsert(
            "seekme_vectors_invalid_meta",
            ids=["v1"],
            vectors=[[1.0, 0.0, 0.0]],
            metadatas=[{"bad": {1, 2}}],
        )
