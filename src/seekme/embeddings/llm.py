"""LLM embedding provider adapter."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from typing import Any

from ..exceptions import ConfigurationError, EmbeddingError, ValidationError
from ..types import Document, Vector
from .base import Embedder


class RemoteEmbedder(Embedder):
    """Embedding provider backed by a hosted embedding API."""

    def __init__(
        self,
        *,
        model: str,
        provider: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        client_args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._model = model
        self._provider = provider
        self._api_key = api_key
        self._api_base = api_base
        self._client_args = client_args
        self._kwargs = kwargs

    def embed(self, texts: Sequence[Document]) -> list[Vector]:
        if not texts:
            return []
        api = _load_llm_api()
        try:
            result = api.embedding(
                self._model,
                list(texts),
                provider=self._provider,
                api_key=self._api_key,
                api_base=self._api_base,
                client_args=self._client_args,
                **self._kwargs,
            )
        except Exception as exc:  # pragma: no cover - depends on provider runtime
            raise EmbeddingError.request_failed() from exc
        try:
            return _normalize_embeddings(result)
        except ValidationError:
            raise
        except Exception as exc:  # pragma: no cover - defensive parsing error
            raise EmbeddingError.response_failed() from exc


def _load_llm_api():
    try:
        any_llm = importlib.import_module("any_llm")
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ConfigurationError.missing_optional_dependency("embeddings") from exc
    return any_llm.api


def _normalize_embeddings(result: Any) -> list[Vector]:
    if isinstance(result, list) and all(isinstance(item, list) for item in result):
        return [[float(x) for x in item] for item in result]
    if isinstance(result, dict) and "data" in result:
        return _from_data_list(result["data"])
    if hasattr(result, "data"):
        return _from_data_list(result.data)
    if isinstance(result, dict) and "embeddings" in result:
        return [[float(x) for x in item] for item in result["embeddings"]]
    raise ValidationError.embedding_response_unsupported()


def _from_data_list(data: Any) -> list[Vector]:
    embeddings: list[Vector] = []
    for item in data:
        if isinstance(item, dict) and "embedding" in item:
            embeddings.append([float(x) for x in item["embedding"]])
        elif hasattr(item, "embedding"):
            embeddings.append([float(x) for x in item.embedding])
        else:
            raise ValidationError.embedding_missing()
    return embeddings


LLMEmbedder = RemoteEmbedder

__all__ = ["LLMEmbedder", "RemoteEmbedder"]
