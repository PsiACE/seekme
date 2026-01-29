"""Embedding provider interfaces."""

from .base import Embedder
from .llm import RemoteEmbedder

__all__ = ["Embedder", "RemoteEmbedder"]
