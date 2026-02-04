"""Shared identifier validation helpers."""

from __future__ import annotations

import re
from .exceptions import ValidationError

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_identifier(value: str) -> bool:
    return bool(_IDENTIFIER_RE.match(value))


def validate_identifier(value: str) -> None:
    if not is_identifier(value):
        raise ValidationError.invalid_identifier(value)


def validate_index_option(name: str, value: object) -> None:
    if not isinstance(value, str) or not is_identifier(value) or value != value.lower():
        raise ValidationError.invalid_index_option(name, value)


def validate_index_property_name(value: object) -> None:
    if not isinstance(value, str) or not is_identifier(value) or value != value.lower():
        raise ValidationError.invalid_index_property_name(str(value))


def validate_index_property_value(name: str, value: object) -> None:
    if not isinstance(value, (str, int, float, bool)):
        raise ValidationError.invalid_index_property_value(name)
    if isinstance(value, str) and not is_identifier(value):
        raise ValidationError.invalid_index_property_value(name)


__all__ = [
    "is_identifier",
    "validate_identifier",
    "validate_index_option",
    "validate_index_property_name",
    "validate_index_property_value",
]
