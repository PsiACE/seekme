"""Utilities for rendering SQL and normalizing rows in seekdb embedded mode."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from ...exceptions import ValidationError

_PARAM_RE = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")


def render_sql(sql: str, params: Mapping[str, Any] | None) -> str:
    if not params:
        return sql

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in params:
            raise ValidationError.missing_sql_parameter(name)
        return _sql_literal(params[name])

    return _PARAM_RE.sub(replace, sql)


def infer_select_columns(sql: str) -> list[str] | None:
    match = re.search(r"SELECT\s+(.+?)\s+FROM", sql, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    select_clause = match.group(1).strip()
    parts: list[str] = []
    depth = 0
    current = ""
    for char in select_clause:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(current.strip())
            current = ""
            continue
        current += char
    if current:
        parts.append(current.strip())
    column_names: list[str] = []
    for part in parts:
        as_match = re.search(r"\s+AS\s+(\w+)", part, re.IGNORECASE)
        if as_match:
            column_names.append(as_match.group(1))
            continue
        raw = part.replace("`", "").strip()
        column_names.append(raw.split()[-1])
    return column_names


def normalize_rows(rows: Any, columns: list[str] | None) -> list[Mapping[str, Any]]:
    if rows is None:
        return []
    if not columns:
        return [row if isinstance(row, dict) else {"value": row} for row in rows]
    return [dict(zip(columns, row, strict=False)) for row in rows]


def normalize_row(row: Any, columns: list[str] | None) -> Mapping[str, Any] | None:
    if row is None:
        return None
    if not columns:
        return row if isinstance(row, dict) else {"value": row}
    return dict(zip(columns, row, strict=False))


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        text = bytes(value).decode("utf-8", errors="replace")
        return f"'{_escape_sql(text)}'"
    return f"'{_escape_sql(str(value))}'"


def _escape_sql(value: str) -> str:
    return value.replace("'", "''")
