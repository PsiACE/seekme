"""End-to-end test for embedded seekdb driver."""

from __future__ import annotations

import sys

import pytest

from seekme import Client


@pytest.mark.e2e
def test_seekdb_embedded_end_to_end(tmp_path) -> None:
    if sys.platform != "linux":
        pytest.skip("pylibseekdb is only available on Linux.")
    pytest.importorskip("pylibseekdb")

    data_dir = tmp_path / "seekdb.db"
    url = f"seekdb:///{data_dir}?database=seekme_test"

    client = Client.from_database_url(url, db_driver="seekdb")
    client.connect()
    assert client.db is not None

    row = client.db.fetch_one("SELECT 1 AS ok")
    assert row == {"ok": 1}

    store = client.vector_store
    assert store is not None
    store.create_collection("seekme_vectors_embedded", dimension=3)
    store.upsert(
        "seekme_vectors_embedded",
        ids=["v1"],
        vectors=[[1.0, 0.0, 0.0]],
        metadatas=[{"lang-code": "en"}],
    )

    results = store.search(
        "seekme_vectors_embedded",
        query=[1.0, 0.0, 0.0],
        top_k=1,
        where={"lang-code": "en"},
        return_fields=["id"],
        include_distance=False,
    )
    assert results == [{"id": "v1"}]
    client.close()
