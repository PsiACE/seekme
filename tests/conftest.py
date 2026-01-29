"""Shared test fixtures for integration tests."""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from dotenv import load_dotenv

from seekme import Client

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
    host = os.getenv("SEEKDB_HOST", "127.0.0.1")
    port = os.getenv("SEEKDB_PORT", "2881")
    user = os.getenv("SEEKDB_USER", "root")
    password = os.getenv("SEEKDB_PASSWORD", "")
    suffix = f"/{database}" if database else "/"
    return f"mysql+pymysql://{user}:{password}@{host}:{port}{suffix}"


@pytest.fixture(scope="session")
def db_name() -> str:
    return os.getenv("SEEKDB_TEST_DATABASE", "seekme_test")


@pytest.fixture(scope="session")
def _ensure_database(db_name: str) -> Iterator[None]:
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
def client(db_name: str, _ensure_database: None) -> Iterator[Client]:
    url = _database_url(db_name)
    try:
        instance = Client.from_database_url(url)
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
    if sys.version_info < (3, 11):
        pytest.skip("Embedding integration tests require Python 3.11+.")

    try:
        __import__("any_llm")
    except ImportError:
        pytest.skip("Embedding provider SDK is not installed.")

    api_key = _env_value("LLM_API_KEY")
    model = _env_value("LLM_MODEL") or "text-embedding-v3"
    api_base = _env_value("LLM_API_BASE") or "https://dashscope.aliyuncs.com/compatible-mode/v1"
    provider = _env_value("LLM_PROVIDER") or "openai"

    if not api_key:
        pytest.skip("Set LLM_API_KEY to run this test.")

    return EmbeddingConfig(
        model=model,
        provider=provider,
        api_key=api_key,
        api_base=api_base,
    )


def _env_value(*keys: str) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return None
