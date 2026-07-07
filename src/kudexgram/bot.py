from __future__ import annotations

import asyncio
import os

from kudexgram.app import Application, Plugin
from kudexgram.client import TelegramClient
from kudexgram.router import Router
from kudexgram.runtime import PollingRunner, PollingUpdateSource
from kudexgram.types import Update


class Bot:
    def __init__(self, token: str, *, client: TelegramClient | None = None) -> None:
        self.app = Application(client=client or TelegramClient(token))

    @classmethod
    def from_env(cls, name: str = "TELEGRAM_BOT_TOKEN") -> Bot:
        token = os.getenv(name)
        if not token:
            raise RuntimeError(f"Environment variable {name} is required")
        return cls(token)

    @property
    def client(self) -> TelegramClient:
        return self.app.client

    def include(self, router: Router) -> None:
        self.app.include(router)

    def install(self, plugin: Plugin) -> None:
        self.app.install(plugin)

    def run_polling(self) -> None:
        asyncio.run(self.polling())

    async def polling(self, *, long_poll_timeout: int = 30) -> None:
        source = PollingUpdateSource(self.client, long_poll_timeout=long_poll_timeout)
        runner = PollingRunner(self.app, source)
        await runner.run_forever()

    async def dispatch(self, update: Update) -> bool:
        return await self.app.dispatch(update)

    async def aclose(self) -> None:
        await self.app.aclose()
