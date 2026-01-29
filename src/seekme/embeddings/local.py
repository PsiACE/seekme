"""Local embedding provider adapter."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from typing import Any

from ..exceptions import ConfigurationError, EmbeddingError, ValidationError
from ..types import Document, Vector
from .base import Embedder


class LocalEmbedder(Embedder):
    """Embedding provider backed by sentence-transformers."""

    def __init__(
        self,
        *,
        model: str,
        device: str | None = None,
        normalize: bool = False,
        batch_size: int | None = None,
        encode_args: dict[str, Any] | None = None,
    ) -> None:
        if not model.strip():
            raise ValidationError.invalid_identifier("model")
        self._model_name = model
        self._device = device
        self._normalize = normalize
        self._batch_size = batch_size
        self._encode_args = encode_args or {}
        self._backend = None

    def embed(self, texts: Sequence[Document]) -> list[Vector]:
        if not texts:
            return []
        backend = self._load_backend()
        kwargs = dict(self._encode_args)
        kwargs["normalize_embeddings"] = self._normalize
        kwargs["show_progress_bar"] = False
        kwargs["convert_to_numpy"] = True
        if self._batch_size is not None:
            kwargs["batch_size"] = self._batch_size
        try:
            outputs = backend.encode(
                list(texts),
                **kwargs,
            )
        except Exception as exc:  # pragma: no cover - depends on runtime backend
            raise EmbeddingError.request_failed() from exc
        try:
            return outputs.tolist()
        except Exception as exc:
            raise EmbeddingError.response_failed() from exc

    def _load_backend(self):
        if self._backend is not None:
            return self._backend
        try:
            sentence_transformers = importlib.import_module("sentence_transformers")
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ConfigurationError.missing_optional_dependency("local-embeddings") from exc
        try:
            backend = sentence_transformers.SentenceTransformer(self._model_name, device=self._device)
        except Exception as exc:  # pragma: no cover - depends on runtime backend
            raise EmbeddingError.request_failed() from exc
        self._backend = backend
        return backend


__all__ = ["LocalEmbedder"]
