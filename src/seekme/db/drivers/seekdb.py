"""Seekdb embedded driver backed by pylibseekdb."""

from __future__ import annotations

import importlib
import os
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from ...exceptions import ConfigurationError, DatabaseError, ValidationError
from ..core import Database
from ._seekdb_sql import infer_select_columns, normalize_row, normalize_rows, render_sql

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_OPENED_PATH: str | None = None


class SeekdbDatabase(Database):
    """Embedded seekdb database implementation."""

    def __init__(self, *, path: str, database: str = "test") -> None:
        self._path = os.path.abspath(path)
        self._database = database
        self._conn: Any | None = None

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> SeekdbDatabase:
        path, database = _parse_seekdb_url(url)
        path = kwargs.pop("path", path)
        database = kwargs.pop("database", database)
        if kwargs:
            raise ValidationError.unsupported_seekdb_options(sorted(kwargs))
        return cls(path=path, database=database)

    def connect(self) -> None:
        if self._conn is not None:
            return
        seekdb = _load_seekdb()
        _ensure_data_path(self._path)
        _open_seekdb(seekdb, self._path)
        try:
            self._conn = seekdb.connect(database=self._database, autocommit=True)
        except Exception as exc:
            if _is_unknown_database(exc):
                _create_database(seekdb, self._database)
                try:
                    self._conn = seekdb.connect(database=self._database, autocommit=True)
                except Exception as retry_exc:
                    raise DatabaseError.connection_failed() from retry_exc
                else:
                    return
            raise DatabaseError.connection_failed() from exc

    def close(self) -> None:
        if self._conn is None:
            return
        try:
            self._conn.close()
        finally:
            self._conn = None

    def execute(self, sql: str, params: Mapping[str, Any] | None = None) -> int:
        conn = self._connection()
        rendered = render_sql(sql, params)
        try:
            cursor = conn.cursor()
            cursor.execute(rendered)
            return int(getattr(cursor, "rowcount", 0))
        except Exception as exc:
            raise DatabaseError.execution_failed() from exc
        finally:
            cursor.close()

    def fetch_all(self, sql: str, params: Mapping[str, Any] | None = None) -> list[Mapping[str, Any]]:
        conn = self._connection()
        rendered = render_sql(sql, params)
        try:
            cursor = conn.cursor()
            cursor.execute(rendered)
            rows = cursor.fetchall()
            description = getattr(cursor, "description", None)
            columns = None
            if description:
                columns = [col[0] for col in description]
            elif rows:
                columns = infer_select_columns(rendered)
            return normalize_rows(rows, columns)
        except Exception as exc:
            raise DatabaseError.fetch_failed() from exc
        finally:
            cursor.close()

    def fetch_one(self, sql: str, params: Mapping[str, Any] | None = None) -> Mapping[str, Any] | None:
        conn = self._connection()
        rendered = render_sql(sql, params)
        try:
            cursor = conn.cursor()
            cursor.execute(rendered)
            row = cursor.fetchone()
            description = getattr(cursor, "description", None)
            columns = None
            if description:
                columns = [col[0] for col in description]
            elif row is not None:
                columns = infer_select_columns(rendered)
            return normalize_row(row, columns)
        except Exception as exc:
            raise DatabaseError.fetch_failed() from exc
        finally:
            cursor.close()

    def begin(self) -> None:
        self._run_transaction_method("begin")

    def commit(self) -> None:
        self._run_transaction_method("commit")

    def rollback(self) -> None:
        self._run_transaction_method("rollback")

    def _run_transaction_method(self, name: str) -> None:
        conn = self._connection()
        method = getattr(conn, name, None)
        if method is None:
            return
        try:
            method()
        except Exception as exc:
            raise DatabaseError.transaction_failed(name) from exc

    def _connection(self) -> Any:
        self.connect()
        if self._conn is None:
            raise DatabaseError.connection_failed()
        return self._conn


def _load_seekdb():
    try:
        return importlib.import_module("pylibseekdb")
    except ImportError as exc:
        raise ConfigurationError.missing_optional_dependency("seekdb") from exc


def _ensure_data_path(path: str) -> None:
    if os.path.exists(path):
        if not os.path.isdir(path):
            raise ValidationError.seekdb_path_not_directory(path)
        return
    os.makedirs(path, exist_ok=True)


def _open_seekdb(seekdb: Any, path: str) -> None:
    global _OPENED_PATH
    if _OPENED_PATH is None:
        try:
            seekdb.open(db_dir=path)
        except Exception as exc:
            if "initialized twice" not in str(exc):
                raise DatabaseError.connection_failed() from exc
        _OPENED_PATH = path
        return
    if os.path.abspath(path) != os.path.abspath(_OPENED_PATH):
        raise ValidationError.seekdb_already_opened(_OPENED_PATH)


def _parse_seekdb_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "seekdb":
        raise ValidationError.invalid_seekdb_url(url)
    raw_path = parsed.netloc + parsed.path
    path = unquote(raw_path).lstrip("/") or "seekdb.db"
    query = parse_qs(parsed.query)
    database = (query.get("database") or ["test"])[0]
    return path, database


def _create_database(seekdb: Any, name: str) -> None:
    _validate_identifier(name)
    try:
        conn = seekdb.connect(database="test", autocommit=True)
    except Exception as exc:
        raise DatabaseError.connection_failed() from exc
    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{name}`")
    except Exception as exc:
        raise DatabaseError.execution_failed() from exc
    finally:
        cursor.close()
        conn.close()


def _is_unknown_database(exc: Exception) -> bool:
    return "Unknown database" in str(exc)


def _validate_identifier(name: str) -> None:
    if not _IDENTIFIER_RE.match(name):
        raise ValidationError.invalid_identifier(name)


__all__ = ["SeekdbDatabase"]
