"""Shared types used across the SDK."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

Document = str
Documents = Sequence[Document]

Vector = Sequence[float]
Vectors = Sequence[Vector]

Metadata = Mapping[str, Any]
Metadatas = Sequence[Metadata]

Id = str
Ids = Sequence[Id]

__all__ = [
    "Document",
    "Documents",
    "Vector",
    "Vectors",
    "Metadata",
    "Metadatas",
    "Id",
    "Ids",
]

