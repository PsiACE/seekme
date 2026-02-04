# User Guide

seekme is an end-to-end seekdb toolchain for AI workflows in-database. It favors a minimal, explicit surface so you can stay close to SQL while adding vector search and optional embeddings.

## Design Principles

- Minimal surface area with one obvious path to connect and query
- Explicit SQL behavior and predictable defaults
- Optional embeddings that never block the core path
- Consistent SDK-level errors instead of leaking driver details
- Clear extension points for custom drivers and vector stores

## Scope and Non-goals

- No embedded engine
- No heavy configuration layer or object graphs
- No schema manager or migration framework (use SQL directly)
- Complex filters should be expressed in SQL

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
# store.delete_vector_index("docs", "idx_vec")

store.upsert(
    "docs",
    ids=["v1", "v2"],
    vectors=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
    metadatas=[{"lang-code": "en"}, {"lang-code": "zh"}],
)

results = store.search(
    "docs",
    query=[1.0, 0.0, 0.0],
    top_k=1,
    distance="l2",
    include_distance=True,
    include_metadata=True,
)
```

### Vector Index Lifecycle

Vector indexes are explicitly managed by the caller. Creation and deletion are separate operations.

```python
from seekme.vector import VectorIndexConfig

store = client.vector_store
store.create_collection("docs", dimension=3)

index = VectorIndexConfig(name="idx_vec", distance="l2", index_type="hnsw", lib="vsag")
store.create_vector_index("docs", index)

results = store.search("docs", query=[1.0, 0.0, 0.0], top_k=3, distance="l2")

store.delete_vector_index("docs", "idx_vec")
```

Supported index types and parameters:

- `hnsw`: optional `m`, `ef_construction`, `ef_search`
- `ivf_flat`: optional `nlist`, `samples_per_nlist`
- `ivf_sq8`: optional `nlist`, `samples_per_nlist`
- `ivf_pq`: requires `m`, optional `nlist`, `samples_per_nlist`

Naming rules:

- `index_type`, `distance`, `lib`, and property keys are lowercase snake_case.

### SQL + Vector + Embeddings (optional)

```python
from seekme.embeddings import RemoteEmbedder

embedder = RemoteEmbedder(model="text-embedding-3-small", provider="openai")
client = Client(db=client.db, embedder=embedder)

results = client.vector_store.search("docs", query="hello world", top_k=3, distance="l2")
```

### SQL + Vector + Local Embeddings (optional)

```python
from seekme.embeddings import LocalEmbedder

embedder = LocalEmbedder(model="sentence-transformers/paraphrase-MiniLM-L3-v2")
client = Client(db=client.db, embedder=embedder)

results = client.vector_store.search("docs", query="hello world", top_k=3, distance="l2")
```

`LocalEmbedder` uses `sentence-transformers` and accepts either a model name or a local path.

### Embedded seekdb (optional)

```python
client = Client.from_database_url("seekdb:////tmp/seekdb.db?database=seekme_test", db_driver="seekdb")
client.connect()
```

## Vector Search Options

`search()` supports explicit result controls:

- `distance`: distance metric or function name (required)
- `include_distance`: include `_distance` in results
- `include_metadata`: include `metadata` in results
- `return_fields`: explicit columns to return (overrides `include_metadata`)
- `where`: metadata equality filters

Notes:
- `return_fields` must contain real table columns (for example `id`, custom columns).
- `include_distance` still controls `_distance` even when `return_fields` is set.
- `distance` is always required. Keep it consistent with the index configuration you chose.
- `where` performs equality filtering on metadata with any string key.
- `where` values set to `None` match missing or null.
- Use SQL directly for complex filters (range/like/logical combinations).

When `query` is a string, the store uses the configured embedder. If no embedder is configured, a clear `ConfigurationError` is raised.

## Errors

seekme maps SQLAlchemy errors to SDK-level exceptions:

- `DatabaseError` for connect, SQL execution, fetch, or transaction failures
- `ConfigurationError` for missing extras, missing embedder, or unregistered extensions
- `EmbeddingError` for embedding request/response failures
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

## Testing

seekme tests are strict about environment configuration. Use `.env.test.example` as a template and
set only the variables that match your target runtime.

Remote mode (MySQL):

- `SEEKME_TEST_DB_MODE=remote`
- `SEEKME_TEST_DB_URL` or
  `SEEKME_TEST_DB_HOST/SEEKME_TEST_DB_PORT/SEEKME_TEST_DB_USER/SEEKME_TEST_DB_PASSWORD/SEEKME_TEST_DB_NAME`

Embedded mode:

- `SEEKME_TEST_DB_MODE=embedded`
- `SEEKME_TEST_SEEKDB_PATH` (optional)

Local embeddings:

- `SEEKME_TEST_LOCAL_EMBEDDING=1`
- `SEEKME_TEST_LOCAL_MODEL`

Remote embeddings (e2e):

- `SEEKME_TEST_REMOTE_EMBEDDING=1`
- `SEEKME_TEST_REMOTE_API_KEY`
- optional `SEEKME_TEST_REMOTE_MODEL/SEEKME_TEST_REMOTE_PROVIDER/SEEKME_TEST_REMOTE_API_BASE`
