from __future__ import annotations

import asyncio
import os
from collections.abc import Callable
from typing import TYPE_CHECKING

from kudexgram.app import Application, Plugin
from kudexgram.client import TelegramClient
from kudexgram.middleware import Middleware, MiddlewareObject
from kudexgram.router import Handler, Router
from kudexgram.runtime import PollingRunner, PollingUpdateSource
from kudexgram.types import Update

if TYPE_CHECKING:
    from kudexgram.testing import BotScenario


class Bot:
    def __init__(self, token: str, *, client: TelegramClient | None = None) -> None:
        self.app = Application(client=client or TelegramClient(token))
        self.router = Router()
        self.include(self.router)

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

    def command(self, name: str) -> Callable[[Handler], Handler]:
        return self.router.command(name)

    def text(self) -> Callable[[Handler], Handler]:
        return self.router.text()

    def callback(self, data: str) -> Callable[[Handler], Handler]:
        return self.router.callback(data)

    def install(self, plugin: Plugin) -> None:
        self.app.install(plugin)

    def use(self, middleware: Middleware | MiddlewareObject) -> None:
        self.app.use(middleware)

    def run_polling(self) -> None:
        asyncio.run(self.polling())

    async def polling(self, *, long_poll_timeout: int = 30) -> None:
        source = PollingUpdateSource(self.client, long_poll_timeout=long_poll_timeout)
        runner = PollingRunner(self.app, source)
        await runner.run_forever()

    async def dispatch(self, update: Update) -> bool:
        return await self.app.dispatch(update)

    def scenario(
        self,
        *,
        chat_id: int = 1,
        user_id: int = 1,
        first_name: str = "Test",
        username: str | None = "test_user",
    ) -> BotScenario:
        from kudexgram.testing import BotScenario

        return BotScenario(
            self,
            chat_id=chat_id,
            user_id=user_id,
            first_name=first_name,
            username=username,
        )

    async def aclose(self) -> None:
        await self.app.aclose()
