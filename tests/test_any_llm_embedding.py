"""Unit tests for any-llm embedding adapter."""

from __future__ import annotations

import sys
import types

from seekme.embeddings import AnyLLMEmbedder


def test_any_llm_adapter_normalizes_data_response(monkeypatch) -> None:
    class Item:
        def __init__(self, embedding):
            self.embedding = embedding

    class Response:
        data = [Item([0.1, 0.2, 0.3]), Item([0.4, 0.5, 0.6])]

    api = types.SimpleNamespace(embedding=lambda *args, **kwargs: Response())
    monkeypatch.setitem(sys.modules, "any_llm", types.SimpleNamespace(api=api))

    provider = AnyLLMEmbedder(model="test-model", provider="test")
    embeddings = provider.embed(["a", "b"])

    assert embeddings == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


def test_any_llm_adapter_accepts_list_response(monkeypatch) -> None:
    api = types.SimpleNamespace(embedding=lambda *args, **kwargs: [[1.0, 2.0]])
    monkeypatch.setitem(sys.modules, "any_llm", types.SimpleNamespace(api=api))

    provider = AnyLLMEmbedder(model="test-model")
    embeddings = provider.embed(["x"])

    assert embeddings == [[1.0, 2.0]]
