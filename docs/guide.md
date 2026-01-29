# User Guide

seekme is an end-to-end seekdb toolchain for AI workflows in-database. It provides a minimal, Pythonic surface with clear defaults, optional embeddings, and explicit extension points without hiding database behavior.

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

store.upsert(
    "docs",
    ids=["v1", "v2"],
    vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
    metadatas=[{"lang": "en"}, {"lang": "zh"}],
)

results = store.search(
    "docs",
    query=[1.0, 0.0, 0.0],
    top_k=1,
    include_distance=True,
    include_metadata=True,
)
```

### SQL + Vector + Embeddings

```python
from seekme.embeddings import LLMEmbedder

embedder = LLMEmbedder(model="text-embedding-3-small", provider="openai")
client = Client(db=client.db, embedder=embedder)

results = client.vector_store.search("docs", query="hello world", top_k=3)
```

## Vector Search Options

`search()` supports explicit result controls:

- `include_distance`: include `_distance` in results
- `include_metadata`: include `metadata` in results
- `return_fields`: explicit columns to return (overrides `include_metadata`)

When `query` is a string, the store uses the configured embedder. If no embedder is configured, a clear `ConfigurationError` is raised.

## Errors

seekme maps SQLAlchemy errors to SDK-level exceptions:

- `DatabaseError` for connect, SQL execution, fetch, or transaction failures
- `ConfigurationError` for missing extras, missing embedder, or unregistered extensions
- `ValidationError` for invalid identifiers or unexpected embedding responses

This keeps error handling consistent without leaking driver details.

## Extensibility

Use the registry to plug in custom drivers or vector stores:

```python
from seekme.registry import register_db_driver

def create_custom_db(url: str, **kwargs):
    ...

register_db_driver("custom", create_custom_db)
```

## Experience Principles

seekme focuses on a consistent, clear user experience with the smallest possible cognitive load.

- One obvious way to connect and execute SQL
- AI-in-database capabilities share one unified experience, not separate products
- Optional capabilities never block the core path
- Explicit errors and predictable defaults

Advanced features can be added later without complicating the core path.
