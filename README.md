# seekme

[![Release](https://img.shields.io/github/v/release/psiace/seekme)](https://img.shields.io/github/v/release/psiace/seekme)
[![Build status](https://img.shields.io/github/actions/workflow/status/psiace/seekme/main.yml?branch=main)](https://github.com/psiace/seekme/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/psiace/seekme/branch/main/graph/badge.svg)](https://codecov.io/gh/psiace/seekme)
[![Commit activity](https://img.shields.io/github/commit-activity/m/psiace/seekme)](https://img.shields.io/github/commit-activity/m/psiace/seekme)
[![License](https://img.shields.io/github/license/psiace/seekme)](https://img.shields.io/github/license/psiace/seekme)

seekme is an end-to-end seekdb toolchain for AI workflows in-database.

## Install

```bash
pip install seekme
```

Optional extras:

```bash
pip install "seekme[mysql]"
pip install "seekme[embeddings]"
```

Notes:
- `seekme[embeddings]` requires Python 3.11+ due to provider SDK requirements.

## Quickstart

```python
from seekme import Client

client = Client.from_database_url("mysql+pymysql://root:@127.0.0.1:2881/seekme_test")
client.connect()

row = client.db.fetch_one("SELECT 1 AS ok")
assert row["ok"] == 1
```

### Vector Search

```python
store = client.vector_store
store.create_collection("docs", dimension=3)
store.upsert(
    "docs",
    ids=["v1", "v2"],
    vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
)

results = store.search("docs", query=[1.0, 0.0, 0.0], top_k=3)
```

### Embeddings (optional)

```python
from seekme.embeddings import LLMEmbedder

embedder = LLMEmbedder(model="text-embedding-3-small", provider="openai")
client = Client(db=client.db, embedder=embedder)

results = client.vector_store.search("docs", query="hello world", top_k=3)
```

## Design Principles

- End-to-end seekdb toolchain for AI workflows in-database
- SQL-first and explicit
- Minimal surface area, no ORM replacement
- Clear error boundaries and optional dependencies
- Extensible via registry for custom drivers and stores

## Documentation

- User guide: https://psiace.github.io/seekme/

## Development

```bash
make install
make check
make test
```
