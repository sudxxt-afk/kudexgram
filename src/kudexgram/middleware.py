from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from kudexgram.context import Context

NextHandler = Callable[[], Awaitable[Any]]
Middleware = Callable[[Context, NextHandler], Awaitable[Any]]


class MiddlewareObject(Protocol):
    async def __call__(self, ctx: Context, next: NextHandler) -> Any: ...

