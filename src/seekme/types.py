"""Shared types used across the SDK."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

Document = str
Documents = Sequence[Document]

Vector = Sequence[float]
Vectors = Sequence[Vector]
VectorQuery = Vector | Document

Metadata = Mapping[str, Any]
Metadatas = Sequence[Metadata]

Id = str
Ids = Sequence[Id]

__all__ = [
    "Document",
    "Documents",
    "Id",
    "Ids",
    "Metadata",
    "Metadatas",
    "Vector",
    "VectorQuery",
    "Vectors",
]
