"""Cursor-based pagination utilities."""

from __future__ import annotations

import base64
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class CursorPage(BaseModel, Generic[T]):
    """Cursor-paginated response wrapper."""

    items: list[T]
    next_cursor: str | None
    prev_cursor: str | None
    total: int
    has_more: bool


def encode_cursor(offset: int) -> str:
    """Encode an offset as an opaque cursor string."""
    return base64.b64encode(f"offset:{offset}".encode()).decode()


def decode_cursor(cursor: str) -> int:
    """Decode a cursor string back to an offset.

    Returns 0 if the cursor is invalid.
    """
    try:
        decoded = base64.b64decode(cursor).decode()
        if decoded.startswith("offset:"):
            return int(decoded[7:])
    except (ValueError, UnicodeDecodeError):
        pass
    return 0
