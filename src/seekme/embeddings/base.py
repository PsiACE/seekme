"""Embedding provider interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from ..types import Document, Vector


@runtime_checkable
class Embedder(Protocol):
    """Protocol for embedding providers."""

    def embed(self, texts: Sequence[Document]) -> list[Vector]:
        """Return embeddings for input texts."""


__all__ = ["Embedder"]
