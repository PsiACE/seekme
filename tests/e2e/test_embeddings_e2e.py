"""End-to-end embedding integration test."""

from __future__ import annotations

import pytest

from seekme import Client
from seekme.embeddings import RemoteEmbedder


@pytest.mark.e2e
def test_embeddings_end_to_end(
    client: Client,
    table_cleanup: list[str],
    embedding_config,
) -> None:
    embedder = RemoteEmbedder(
        model=embedding_config.model,
        provider=embedding_config.provider,
        api_key=embedding_config.api_key,
        api_base=embedding_config.api_base,
    )
    sdk = Client(db=client.db, embedder=embedder)

    vectors = embedder.embed(["hello", "world"])
    assert vectors
    dimension = len(vectors[0])

    store = sdk.vector_store
    assert store is not None
    table_name = "seekme_vectors_e2e"
    store.create_collection(table_name, dimension=dimension)
    table_cleanup.append(table_name)

    store.upsert(
        table_name,
        ids=["v1", "v2"],
        vectors=vectors,
        metadatas=[{"source": "hello"}, {"source": "world"}],
    )

    results = store.search(table_name, query="hello", top_k=1, distance="l2")
    assert results
    assert "_distance" in results[0]
