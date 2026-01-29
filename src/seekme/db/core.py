"""Core database interfaces and primitives."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class Database(ABC):
    """Abstract database interface for executing SQL and managing transactions."""

    @abstractmethod
    def connect(self) -> None:
        """Open the underlying connection."""

    @abstractmethod
    def close(self) -> None:
        """Close the underlying connection."""

    @abstractmethod
    def execute(self, sql: str, params: Mapping[str, Any] | None = None) -> int:
        """Execute a statement and return affected row count."""

    @abstractmethod
    def fetch_all(self, sql: str, params: Mapping[str, Any] | None = None) -> list[Mapping[str, Any]]:
        """Execute a query and return all rows."""

    @abstractmethod
    def fetch_one(self, sql: str, params: Mapping[str, Any] | None = None) -> Mapping[str, Any] | None:
        """Execute a query and return one row."""

    @abstractmethod
    def begin(self) -> None:
        """Begin a transaction."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""


__all__ = ["Database"]
