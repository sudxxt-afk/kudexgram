from __future__ import annotations

from typing import Protocol

from kudexgram.app import Application
from kudexgram.client import TelegramClient
from kudexgram.types import Update, convert_update


class UpdateSource(Protocol):
    async def fetch(self) -> list[Update]: ...
    async def commit(self, update: Update) -> None: ...


class PollingUpdateSource:
    def __init__(
        self,
        client: TelegramClient,
        *,
        offset: int | None = None,
        long_poll_timeout: int = 30,
        limit: int = 100,
    ) -> None:
        self.client = client
        self.offset = offset
        self.long_poll_timeout = long_poll_timeout
        self.limit = limit

    async def fetch(self) -> list[Update]:
        raw_updates = await self.client.get_updates(
            offset=self.offset,
            long_poll_timeout=self.long_poll_timeout,
            limit=self.limit,
        )
        return [convert_update(raw_update) for raw_update in raw_updates]

    async def commit(self, update: Update) -> None:
        next_offset = update.update_id + 1
        if self.offset is None or next_offset > self.offset:
            self.offset = next_offset


class PollingRunner:
    def __init__(self, app: Application, source: UpdateSource) -> None:
        self.app = app
        self.source = source

    async def run_once(self) -> int:
        updates = await self.source.fetch()
        for update in updates:
            try:
                await self.app.dispatch(update)
            except Exception:
                import sys
                import traceback
                traceback.print_exc(file=sys.stderr)
            finally:
                await self.source.commit(update)
        return len(updates)

    async def run_forever(self) -> None:
        try:
            while True:
                await self.run_once()
        finally:
            await self.app.aclose()

