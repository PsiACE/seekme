"""SQL core implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.engine import Connection, Engine, Transaction
from sqlalchemy.exc import SQLAlchemyError

from ...exceptions import DatabaseError
from ..core import Database


class SQLDatabase(Database):
    """Database implementation backed by a SQL engine."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._conn: Connection | None = None
        self._tx: Transaction | None = None
        self._install_transaction_hooks()

    @classmethod
    def from_url(cls, url: str, **engine_kwargs: Any) -> SQLDatabase:
        from sqlalchemy import create_engine

        engine = create_engine(url, **engine_kwargs)
        return cls(engine)

    def connect(self) -> None:
        if self._conn is None:
            try:
                self._conn = self._engine.connect()
            except SQLAlchemyError as exc:
                raise DatabaseError.connection_failed() from exc

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute(self, sql: str, params: Mapping[str, Any] | None = None) -> int:
        conn = self._connection()
        try:
            result = conn.execute(text(sql), params or {})
        except SQLAlchemyError as exc:
            raise DatabaseError.execution_failed() from exc
        else:
            return result.rowcount

    def fetch_all(self, sql: str, params: Mapping[str, Any] | None = None) -> list[Mapping[str, Any]]:
        conn = self._connection()
        try:
            result = conn.execute(text(sql), params or {})
        except SQLAlchemyError as exc:
            raise DatabaseError.fetch_failed() from exc
        else:
            return [dict(row) for row in result.mappings().all()]

    def fetch_one(self, sql: str, params: Mapping[str, Any] | None = None) -> Mapping[str, Any] | None:
        conn = self._connection()
        try:
            result = conn.execute(text(sql), params or {})
            row = result.mappings().first()
        except SQLAlchemyError as exc:
            raise DatabaseError.fetch_failed() from exc
        else:
            return dict(row) if row else None

    def begin(self) -> None:
        conn = self._connection()
        try:
            if self._tx is None and not conn.in_transaction():
                self._tx = conn.begin()
        except SQLAlchemyError as exc:
            raise DatabaseError.transaction_failed("begin") from exc

    def commit(self) -> None:
        conn = self._connection()
        try:
            if self._tx is not None:
                self._tx.commit()
                self._tx = None
                return
            conn.commit()
        except SQLAlchemyError as exc:
            raise DatabaseError.transaction_failed("commit") from exc

    def rollback(self) -> None:
        conn = self._connection()
        try:
            if self._tx is not None:
                self._tx.rollback()
                self._tx = None
                return
            conn.rollback()
        except SQLAlchemyError as exc:
            raise DatabaseError.transaction_failed("rollback") from exc

    def _connection(self) -> Connection:
        self.connect()
        if self._conn is None:
            raise DatabaseError.connection_failed()
        return self._conn

    def _install_transaction_hooks(self) -> None:
        @event.listens_for(self._engine, "begin")
        def _start_transaction(connection: Connection) -> None:
            if not connection.in_transaction():
                connection.exec_driver_sql("START TRANSACTION")


__all__ = ["SQLDatabase"]
