"""Shared test fixtures for integration tests."""

from __future__ import annotations

import logging
import os
import sys
import types
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from dotenv import load_dotenv

from seekme import Client
from seekme.embeddings import LocalEmbedder

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmbeddingConfig:
    model: str
    provider: str | None
    api_key: str | None
    api_base: str | None


@pytest.fixture(scope="session", autouse=True)
def _load_env() -> None:
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env", override=False)


def _database_url(database: str | None) -> str:
    host = os.getenv("SEEKME_TEST_DB_HOST") or "127.0.0.1"
    port = os.getenv("SEEKME_TEST_DB_PORT") or "2881"
    user = os.getenv("SEEKME_TEST_DB_USER") or "root"
    password = os.getenv("SEEKME_TEST_DB_PASSWORD") or ""
    suffix = f"/{database}" if database else "/"
    return f"mysql+pymysql://{user}:{password}@{host}:{port}{suffix}"


@pytest.fixture(scope="session")
def db_name() -> str:
    return os.getenv("SEEKME_TEST_DB_NAME") or "seekme_test"


@pytest.fixture(scope="session")
def db_mode() -> str:
    value = os.getenv("SEEKME_TEST_DB_MODE") or "remote"
    return value.strip().lower()


def _seekdb_url(path: str, database: str) -> str:
    return f"seekdb:///{path}?database={database}"


@pytest.fixture(scope="session")
def _ensure_database(db_name: str, db_mode: str) -> Iterator[None]:
    if _is_embedded_mode(db_mode):
        yield
        return
    from sqlalchemy import create_engine

    engine = create_engine(_database_url(None))
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
    except Exception as exc:  # pragma: no cover - requires live database
        engine.dispose()
        pytest.skip(f"SeekDB is not available: {exc}")
    else:
        try:
            yield
        finally:
            try:
                with engine.connect() as conn:
                    conn.exec_driver_sql(f"DROP DATABASE IF EXISTS `{db_name}`")
            except Exception as exc:  # pragma: no cover - requires live database
                logger.debug("Failed to drop test database: %s", exc)
            engine.dispose()


@pytest.fixture(scope="session")
def client(db_name: str, db_mode: str, _ensure_database: None) -> Iterator[Client]:
    if _is_embedded_mode(db_mode):
        yield from _create_embedded_client(db_name)
    else:
        yield from _create_remote_client(db_name, db_mode)


def _create_client(url: str, db_driver: str | None) -> Iterator[Client]:
    try:
        if db_driver is None:
            instance = Client.from_database_url(url)
        else:
            instance = Client.from_database_url(url, db_driver=db_driver)
        instance.connect()
    except Exception as exc:  # pragma: no cover - requires live database
        pytest.skip(f"SeekDB is not available: {exc}")
    assert instance.db is not None
    yield instance
    instance.close()


@pytest.fixture()
def db(client: Client) -> Iterator[Client]:
    yield client


@pytest.fixture()
def table_cleanup(client: Client) -> Iterator[list[str]]:
    tables: list[str] = []
    yield tables
    if not tables:
        return
    assert client.db is not None
    for table in tables:
        client.db.execute(f"DROP TABLE IF EXISTS {table}")
    client.db.commit()


@pytest.fixture(scope="session")
def embedding_config() -> EmbeddingConfig:
    available, reason = _remote_embedding_available()
    if not available:
        pytest.skip(reason)

    api_key = os.getenv("SEEKME_TEST_REMOTE_API_KEY")
    model = os.getenv("SEEKME_TEST_REMOTE_MODEL") or "text-embedding-v3"
    api_base = os.getenv("SEEKME_TEST_REMOTE_API_BASE") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    provider = os.getenv("SEEKME_TEST_REMOTE_PROVIDER") or "openai"

    return EmbeddingConfig(
        model=model,
        provider=provider,
        api_key=api_key,
        api_base=api_base,
    )


@pytest.fixture(scope="session")
def local_embedder() -> LocalEmbedder:
    available, reason = _local_embedding_available()
    if not available:
        pytest.skip(reason)

    model = os.getenv("SEEKME_TEST_LOCAL_MODEL") or "sentence-transformers/paraphrase-MiniLM-L3-v2"
    return LocalEmbedder(model=model, normalize=False, device="cpu")


def _has_module(name: str) -> bool:
    try:
        __import__(name)
    except ImportError:
        return False
    return True


def _is_embedded_mode(value: str) -> bool:
    return value == "embedded"


def _create_embedded_client(db_name: str) -> Iterator[Client]:
    if sys.platform != "linux":
        pytest.skip("pylibseekdb is only available on Linux.")
    if not _has_module("pylibseekdb"):
        pytest.skip("pylibseekdb is not installed.")

    path = os.getenv("SEEKME_TEST_SEEKDB_PATH")
    if path is None:
        with TemporaryDirectory() as tmp_dir:
            url = _seekdb_url(tmp_dir, db_name)
            yield from _create_client(url, db_driver="seekdb")
        return
    url = _seekdb_url(path, db_name)
    yield from _create_client(url, db_driver="seekdb")


def _create_remote_client(db_name: str, db_mode: str) -> Iterator[Client]:
    if db_mode != "remote":
        pytest.fail("Unsupported SEEKME_TEST_DB_MODE")
    url = os.getenv("SEEKME_TEST_DB_URL") or _database_url(db_name)
    yield from _create_client(url, db_driver=None)


def _remote_embedding_available() -> tuple[bool, str]:
    if sys.version_info < (3, 11):
        return False, "Embedding integration tests require Python 3.11+."
    if not _env_flag("SEEKME_TEST_REMOTE_EMBEDDING"):
        return False, "Remote embedding tests are disabled."
    if not _has_module("any_llm"):
        return False, "Embedding provider SDK is not installed."
    if not os.getenv("SEEKME_TEST_REMOTE_API_KEY"):
        return False, "Set SEEKME_TEST_REMOTE_API_KEY to run this test."
    return True, ""


def _local_embedding_available() -> tuple[bool, str]:
    if not _env_flag("SEEKME_TEST_LOCAL_EMBEDDING"):
        return False, "Local embedding tests are disabled."
    if not _has_module("sentence_transformers"):
        return False, "Local embeddings extras are not installed."
    return True, ""


def _env_flag(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


@pytest.fixture()
def local_embedder_mock(monkeypatch) -> tuple[LocalEmbedder, dict[str, object]]:
    calls: dict[str, object] = {}

    class DummyOutputs:
        def __init__(self, data: list[list[float]]):
            self._data = data

        def tolist(self) -> list[list[float]]:
            return self._data

    class DummyModel:
        def __init__(self, model, device=None):
            calls["model"] = model
            calls["device"] = device

        def encode(self, texts, **kwargs):
            calls["encode"] = kwargs
            data = [[1.0, 1.0, 1.0, 1.0] for _ in texts]
            return DummyOutputs(data)

    fake_module = types.SimpleNamespace(SentenceTransformer=DummyModel)
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)

    embedder = LocalEmbedder(
        model="test-model",
        device="cpu",
        normalize=True,
        batch_size=4,
    )
    return embedder, calls
