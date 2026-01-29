"""Unit tests for embedding adapter."""

from __future__ import annotations

import sys
import types
from typing import ClassVar, cast

import pytest

from seekme.embeddings import LocalEmbedder, RemoteEmbedder
from seekme.exceptions import EmbeddingError


def test_remote_adapter_normalizes_data_response(monkeypatch) -> None:
    class Item:
        def __init__(self, embedding):
            self.embedding = embedding

    class Response:
        data: ClassVar[list[Item]] = [Item([0.1, 0.2, 0.3]), Item([0.4, 0.5, 0.6])]

    api = types.SimpleNamespace(embedding=lambda *args, **kwargs: Response())
    monkeypatch.setitem(sys.modules, "any_llm", types.SimpleNamespace(api=api))

    provider = RemoteEmbedder(model="test-model", provider="test")
    embeddings = provider.embed(["a", "b"])

    assert embeddings == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_remote_adapter_accepts_list_response(monkeypatch) -> None:
    api = types.SimpleNamespace(embedding=lambda *args, **kwargs: [[1.0, 2.0]])
    monkeypatch.setitem(sys.modules, "any_llm", types.SimpleNamespace(api=api))

    provider = RemoteEmbedder(model="test-model")
    embeddings = provider.embed(["x"])

    assert embeddings == [[1.0, 2.0]]


def test_remote_adapter_wraps_provider_error(monkeypatch) -> None:
    class ProviderFailure(RuntimeError):
        """Provider failure."""

    def _raise(*args, **kwargs):
        raise ProviderFailure

    api = types.SimpleNamespace(embedding=_raise)
    monkeypatch.setitem(sys.modules, "any_llm", types.SimpleNamespace(api=api))

    provider = RemoteEmbedder(model="test-model")

    with pytest.raises(EmbeddingError, match="Embedding request failed"):
        provider.embed(["x"])


def test_local_embedder_returns_vectors(local_embedder_mock: tuple[LocalEmbedder, dict[str, object]]) -> None:
    embedder, calls = local_embedder_mock
    embeddings = embedder.embed(["hello", "world"])
    assert embeddings == [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]]
    assert calls["model"] == "test-model"
    assert calls["device"] == "cpu"
    encode_calls = cast(dict[str, object], calls["encode"])
    assert encode_calls["normalize_embeddings"] is True
