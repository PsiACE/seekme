"""Embedding provider interfaces."""

from .base import Embedder
from .local import LocalEmbedder
from .remote import RemoteEmbedder

__all__ = ["Embedder", "LocalEmbedder", "RemoteEmbedder"]
