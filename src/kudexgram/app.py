from __future__ import annotations

from typing import Protocol

from kudexgram.client import TelegramClient
from kudexgram.router import Router
from kudexgram.types import Update


class Plugin(Protocol):
    def setup(self, app: Application) -> None: ...


class Application:
    def __init__(self, *, client: TelegramClient) -> None:
        self.client = client
        self.routers: list[Router] = []
        self.plugins: list[Plugin] = []

    def include(self, router: Router) -> None:
        self.routers.append(router)

    def install(self, plugin: Plugin) -> None:
        plugin.setup(self)
        self.plugins.append(plugin)

    async def dispatch(self, update: Update) -> bool:
        for router in self.routers:
            if await router.dispatch(update, self.client):
                return True
        return False

    async def aclose(self) -> None:
        await self.client.aclose()

