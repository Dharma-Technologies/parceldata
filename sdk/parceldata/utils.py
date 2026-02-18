"""Helper utilities for the ParcelData SDK."""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def run_sync(coro: object) -> object:
    """Run an async coroutine synchronously.

    Uses the existing event loop if available, otherwise creates a new one.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future: concurrent.futures.Future[object] = pool.submit(asyncio.run, coro)  # type: ignore[arg-type]
            return future.result()
    else:
        return asyncio.run(coro)  # type: ignore[arg-type]


def build_query_params(**kwargs: object) -> dict[str, str]:
    """Build query parameters dict, omitting None values."""
    params: dict[str, str] = {}
    for key, value in kwargs.items():
        if value is not None:
            params[key] = str(value)
    return params


def retry_delays(
    max_retries: int,
    base_delay: float = 0.5,
) -> Callable[[], list[float]]:
    """Generate exponential backoff delay sequence."""

    def _delays() -> list[float]:
        return [base_delay * (2**i) for i in range(max_retries)]

    return _delays
