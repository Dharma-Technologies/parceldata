"""Tests for cursor-based pagination utilities."""

from __future__ import annotations

from app.utils.pagination import (
    CursorPage,
    decode_cursor,
    encode_cursor,
)


class TestCursorEncoding:
    def test_encode_decode_roundtrip(self) -> None:
        cursor = encode_cursor(25)
        assert decode_cursor(cursor) == 25

    def test_encode_zero(self) -> None:
        cursor = encode_cursor(0)
        assert decode_cursor(cursor) == 0

    def test_decode_invalid(self) -> None:
        assert decode_cursor("invalid") == 0

    def test_decode_empty(self) -> None:
        assert decode_cursor("") == 0

    def test_encode_large_offset(self) -> None:
        cursor = encode_cursor(10000)
        assert decode_cursor(cursor) == 10000


class TestCursorPage:
    def test_page_with_items(self) -> None:
        page = CursorPage[str](
            items=["a", "b", "c"],
            next_cursor=encode_cursor(3),
            prev_cursor=None,
            total=10,
            has_more=True,
        )
        assert len(page.items) == 3
        assert page.has_more is True
        assert page.total == 10
        assert page.next_cursor is not None

    def test_last_page(self) -> None:
        page = CursorPage[str](
            items=["x"],
            next_cursor=None,
            prev_cursor=encode_cursor(0),
            total=1,
            has_more=False,
        )
        assert page.has_more is False
        assert page.next_cursor is None
