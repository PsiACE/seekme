# seekme

[![Release](https://img.shields.io/github/v/release/psiace/seekme)](https://img.shields.io/github/v/release/psiace/seekme)
[![Build status](https://img.shields.io/github/actions/workflow/status/psiace/seekme/main.yml?branch=main)](https://github.com/psiace/seekme/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/psiace/seekme/branch/main/graph/badge.svg)](https://codecov.io/gh/psiace/seekme)
[![Commit activity](https://img.shields.io/github/commit-activity/m/psiace/seekme)](https://img.shields.io/github/commit-activity/m/psiace/seekme)
[![License](https://img.shields.io/github/license/psiace/seekme)](https://img.shields.io/github/license/psiace/seekme)

seekme is an end-to-end seekdb toolchain for AI workflows in-database. It keeps a minimal, explicit surface so you can stay close to SQL while adding vector search and optional embeddings.

## Disclosure

This is not an official OceanBase library. It was developed by the author while employed at OceanBase, and I hope you enjoy it.

## Install

```bash
pip install seekme
```

Optional extras:

```bash
pip install "seekme[mysql]"
pip install "seekme[remote-embeddings]"
pip install "seekme[local-embeddings]"
pip install "seekme[seekdb]"
```

Notes:
- `seekme[remote-embeddings]` requires Python 3.11+ due to provider SDK requirements.
- `seekme[local-embeddings]` installs sentence-transformers.
- `seekme[seekdb]` requires Linux and installs pylibseekdb for embedded mode.

## Quickstart

### SQL-only

```python
from seekme import Client

client = Client.from_database_url("mysql+pymysql://root:@127.0.0.1:2881/seekme_test")
client.connect()

row = client.db.fetch_one("SELECT 1 AS ok")
assert row["ok"] == 1
```

### SQL + Vector

```python
store = client.vector_store
store.create_collection("docs", dimension=3)
# Optional: create vector index explicitly
# from seekme.vector import VectorIndexConfig
# index = VectorIndexConfig(name="idx_vec", distance="l2", index_type="hnsw", lib="vsag")
# store.create_vector_index("docs", index)
store.upsert(
    "docs",
    ids=["v1", "v2"],
    vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
)

results = store.search("docs", query=[1.0, 0.0, 0.0], top_k=3, distance="l2")
```

### SQL + Vector + Embeddings

```python
from seekme.embeddings import LocalEmbedder

embedder = LocalEmbedder(model="sentence-transformers/paraphrase-MiniLM-L3-v2")
sdk = Client(db=client.db, embedder=embedder)

results = sdk.vector_store.search("docs", query="hello world", top_k=3, distance="l2")
```

### Embedded seekdb (optional)

```python
client = Client.from_database_url("seekdb:////tmp/seekdb.db?database=seekme_test", db_driver="seekdb")
client.connect()
```

## Documentation

- User guide: https://psiace.github.io/seekme/

## Development

```bash
make install
make check
make test
```

Test matrix (strict envs):

- Remote mode (MySQL): set `SEEKME_TEST_DB_MODE=remote` with either `SEEKME_TEST_DB_URL` or
  `SEEKME_TEST_DB_HOST/SEEKME_TEST_DB_PORT/SEEKME_TEST_DB_USER/SEEKME_TEST_DB_PASSWORD/SEEKME_TEST_DB_NAME`.
- Embedded mode: set `SEEKME_TEST_DB_MODE=embedded` and `SEEKME_TEST_SEEKDB_PATH` (optional).
- Local embeddings: set `SEEKME_TEST_LOCAL_EMBEDDING=1` and `SEEKME_TEST_LOCAL_MODEL`.
- Remote embeddings (e2e): set `SEEKME_TEST_REMOTE_EMBEDDING=1` and `SEEKME_TEST_REMOTE_API_KEY`
  (optional `SEEKME_TEST_REMOTE_MODEL/SEEKME_TEST_REMOTE_PROVIDER/SEEKME_TEST_REMOTE_API_BASE`).

Use `.env.test.example` as a starting point for local runs.

## License

Apache-2.0. See `LICENSE`.
