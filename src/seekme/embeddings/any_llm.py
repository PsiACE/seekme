"""Any-LLM embedding provider adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .base import Embedder
from ..types import Document, Vector


class AnyLLMEmbedder(Embedder):
    """Embedding provider backed by any-llm."""

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
        api = _load_any_llm_api()
        result = api.embedding(
            self._model,
            list(texts),
            provider=self._provider,
            api_key=self._api_key,
            api_base=self._api_base,
            client_args=self._client_args,
            **self._kwargs,
        )
        return _normalize_embeddings(result)


def _load_any_llm_api():
    try:
        import any_llm
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("any-llm is required. Install with: pip install any-llm-sdk") from exc
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
    raise TypeError("Unsupported any-llm embedding response format.")


def _from_data_list(data: Any) -> list[Vector]:
    embeddings: list[Vector] = []
    for item in data:
        if isinstance(item, dict) and "embedding" in item:
            embeddings.append([float(x) for x in item["embedding"]])
        elif hasattr(item, "embedding"):
            embeddings.append([float(x) for x in item.embedding])
        else:
            raise TypeError("Embedding item missing embedding field.")
    return embeddings


__all__ = ["AnyLLMEmbedder"]
