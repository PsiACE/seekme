"""SQLAlchemy core implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.engine import Connection, Engine, Transaction

from ..core import Database


class SQLAlchemyDatabase(Database):
    """Database implementation backed by a SQLAlchemy engine."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._conn: Connection | None = None
        self._tx: Transaction | None = None
        self._install_transaction_hooks()

    def connect(self) -> None:
        if self._conn is None:
            self._conn = self._engine.connect()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute(self, sql: str, params: Mapping[str, Any] | None = None) -> int:
        conn = self._connection()
        result = conn.execute(text(sql), params or {})
        return result.rowcount

    def fetch_all(self, sql: str, params: Mapping[str, Any] | None = None) -> list[Mapping[str, Any]]:
        conn = self._connection()
        result = conn.execute(text(sql), params or {})
        return [dict(row) for row in result.mappings().all()]

    def fetch_one(self, sql: str, params: Mapping[str, Any] | None = None) -> Mapping[str, Any] | None:
        conn = self._connection()
        result = conn.execute(text(sql), params or {})
        row = result.mappings().first()
        return dict(row) if row else None

    def begin(self) -> None:
        conn = self._connection()
        if self._tx is None and not conn.in_transaction():
            self._tx = conn.begin()

    def commit(self) -> None:
        conn = self._connection()
        if self._tx is not None:
            self._tx.commit()
            self._tx = None
            return
        conn.commit()

    def rollback(self) -> None:
        conn = self._connection()
        if self._tx is not None:
            self._tx.rollback()
            self._tx = None
            return
        conn.rollback()

    def _connection(self) -> Connection:
        self.connect()
        if self._conn is None:
            raise RuntimeError("Connection is not available.")
        return self._conn

    def _install_transaction_hooks(self) -> None:
        @event.listens_for(self._engine, "begin")
        def _start_transaction(connection: Connection) -> None:
            if not connection.in_transaction():
                connection.exec_driver_sql("START TRANSACTION")


__all__ = ["SQLAlchemyDatabase"]
