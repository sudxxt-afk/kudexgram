from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from kudexgram.client import TelegramClient
from kudexgram.context import Context, _current_context
from kudexgram.middleware import Middleware, MiddlewareObject
from kudexgram.router import Router
from kudexgram.types import Update


class Plugin(Protocol):
    def setup(self, app: Application) -> None: ...


class Application:
    def __init__(self, *, client: TelegramClient) -> None:
        self.client = client
        self.routers: list[Router] = []
        self.plugins: list[Plugin] = []
        self.middlewares: list[Middleware | MiddlewareObject] = []

    def include(self, router: Router) -> None:
        self.routers.append(router)

    def install(self, plugin: Plugin) -> None:
        plugin.setup(self)
        self.plugins.append(plugin)

    def use(self, middleware: Middleware | MiddlewareObject) -> None:
        self.middlewares.append(middleware)

    async def dispatch(self, update: Update) -> bool:
        context = Context(update=update, client=self.client)

        async def dispatch_routes() -> bool:
            for router in self.routers:
                if await router.dispatch(context):
                    return True
            return False

        token = _current_context.set(context)
        try:
            return bool(await self._call_middlewares(context, dispatch_routes))
        finally:
            _current_context.reset(token)

    async def _call_middlewares(
        self,
        context: Context,
        dispatch_routes: Callable[[], Awaitable[bool]],
    ) -> bool:
        async def call_at(index: int) -> Any:
            if index >= len(self.middlewares):
                return await dispatch_routes()

            middleware = self.middlewares[index]

            async def next_handler() -> Any:
                return await call_at(index + 1)

            return await middleware(context, next_handler)

        return bool(await call_at(0))

    async def dispatch_without_middleware(self, update: Update) -> bool:
        for router in self.routers:
            context = Context(update=update, client=self.client)
            token = _current_context.set(context)
            try:
                handled = await router.dispatch(context)
            finally:
                _current_context.reset(token)
            if handled:
                return True
        return False

    async def aclose(self) -> None:
        await self.client.aclose()
