# seekme

seekme is an end-to-end seekdb toolchain for AI workflows in-database. It keeps a minimal, explicit surface so you can stay close to SQL while adding vector search and optional embeddings.

## Why seekme

- Minimal surface area with one obvious path to connect and query
- Explicit SQL behavior and predictable defaults
- Optional embeddings that never block the core path
- Consistent SDK-level errors instead of leaking driver details
- Clear extension points for custom drivers and vector stores

## Feature snapshot

- SQL execution with a unified client
- Vector collections backed by SQL tables
- Optional embeddings via provider SDKs

## Quickstart (30s)

```python
from seekme import Client

client = Client.from_database_url("mysql+pymysql://root:@127.0.0.1:2881/seekme_test")
client.connect()

store = client.vector_store
store.create_collection("docs", dimension=3)
store.upsert("docs", ids=["v1"], vectors=[[1.0, 0.0, 0.0]])

results = store.search("docs", query=[1.0, 0.0, 0.0], top_k=1)
```

## When to use seekme

seekme is designed for applications that want a clean SDK for SQL + vector search without a heavy configuration layer.

If you need complex filtering logic, advanced query planning, or schema management, use SQL directly and keep seekme focused on the core path.

## Quick Links

- [User Guide](guide.md)
- [API Reference](modules.md)
