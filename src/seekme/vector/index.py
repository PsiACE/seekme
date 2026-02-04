"""Vector index configuration primitives."""

from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import ValidationError
from ..identifiers import (
    validate_identifier,
    validate_index_option,
    validate_index_property_name,
    validate_index_property_value,
)

_INDEX_PARAM_RULES: dict[str, dict[str, set[str]]] = {
    "hnsw": {"allowed": {"m", "ef_construction", "ef_search"}, "required": set()},
    "ivf_flat": {"allowed": {"nlist", "samples_per_nlist"}, "required": set()},
    "ivf_sq8": {"allowed": {"nlist", "samples_per_nlist"}, "required": set()},
    "ivf_pq": {"allowed": {"m", "nlist", "samples_per_nlist"}, "required": {"m"}},
}

_INDEX_INT_PARAMS = {"m", "ef_construction", "ef_search", "nlist", "samples_per_nlist"}


@dataclass(frozen=True)
class VectorIndexConfig:
    """Explicit vector index configuration.

    All fields are required to keep index behavior explicit.
    """

    name: str
    distance: str
    index_type: str
    lib: str
    properties: dict[str, str | int | float | bool] | None = None

    def __post_init__(self) -> None:
        validate_identifier(self.name)
        validate_index_option("distance", self.distance)
        validate_index_option("index_type", self.index_type)
        validate_index_option("lib", self.lib)
        _validate_index_type(self.index_type)
        _validate_index_properties(self.index_type, self.properties)

    def render_create_sql(self, collection: str, *, column: str = "embedding") -> str:
        validate_identifier(collection)
        validate_identifier(column)
        params = self._render_params()
        return (
            f"CREATE VECTOR INDEX {self.name} ON {collection} ({column}) "
            f"WITH ({params})"
        )

    def _render_params(self) -> str:
        parts = [
            f"DISTANCE={self.distance}",
            f"TYPE={self.index_type}",
            f"LIB={self.lib}",
        ]
        properties = _render_index_properties(self.properties)
        if properties:
            parts.extend(properties)
        return ", ".join(parts)


def _validate_index_type(index_type: str) -> None:
    if index_type not in _INDEX_PARAM_RULES:
        raise ValidationError.unsupported_index_option("index_type", index_type)


def _validate_index_properties(
    index_type: str,
    properties: dict[str, str | int | float | bool] | None,
) -> None:
    if properties is None:
        required = _INDEX_PARAM_RULES[index_type]["required"]
        if required:
            raise ValidationError.missing_index_property(index_type, sorted(required)[0])
        return
    rules = _INDEX_PARAM_RULES[index_type]
    allowed = rules["allowed"]
    required = rules["required"]
    for key in required:
        if key not in properties:
            raise ValidationError.missing_index_property(index_type, key)
    for key, value in properties.items():
        if key not in allowed:
            raise ValidationError.unsupported_index_property(index_type, key)
        validate_index_property_name(key)
        validate_index_property_value(key, value)
        if key in _INDEX_INT_PARAMS and not isinstance(value, int):
            raise ValidationError.invalid_index_property_value(key)
        if key in _INDEX_INT_PARAMS and isinstance(value, int) and value <= 0:
            raise ValidationError.invalid_index_property_value(key)


def _render_index_properties(
    properties: dict[str, str | int | float | bool] | None,
) -> list[str]:
    if not properties:
        return []
    parts: list[str] = []
    for key, value in properties.items():
        if isinstance(value, str):
            parts.append(f"{key}='{value}'")
        else:
            parts.append(f"{key}={value}")
    return parts
