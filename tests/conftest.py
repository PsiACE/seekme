"""Shared test fixtures for integration tests."""

from __future__ import annotations

import os
from typing import Iterator

import pytest

from seekme import Client


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
        yield
    finally:
        with engine.connect() as conn:
            conn.exec_driver_sql(f"DROP DATABASE IF EXISTS `{db_name}`")
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
