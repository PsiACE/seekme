"""Vector storage interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

from ..types import Ids, VectorQuery, Vectors

if TYPE_CHECKING:
    from .index import VectorIndexConfig


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    def create_collection(self, name: str, dimension: int) -> None:
        """Create a vector collection."""

    @abstractmethod
    def delete_collection(self, name: str) -> None:
        """Delete a vector collection."""

    @abstractmethod
    def create_vector_index(self, collection: str, index: VectorIndexConfig) -> None:
        """Create a vector index for a collection."""

    @abstractmethod
    def delete_vector_index(self, collection: str, name: str) -> None:
        """Delete a vector index from a collection."""

    @abstractmethod
    def upsert(
        self,
        collection: str,
        ids: Ids,
        vectors: Vectors,
        metadatas: Sequence[Mapping[str, Any]] | None = None,
    ) -> None:
        """Insert or update vectors."""

    @abstractmethod
    def search(
        self,
        collection: str,
        query: VectorQuery,
        top_k: int,
        *,
        distance: str,
        where: Mapping[str, Any] | None = None,
        return_fields: Sequence[str] | None = None,
        include_distance: bool = True,
        include_metadata: bool = True,
    ) -> list[Mapping[str, Any]]:
        """Search the vector store and return results.

        When return_fields is provided, include_metadata is ignored.
        include_distance remains effective and adds `_distance` when enabled.
        """


__all__ = ["VectorStore"]
