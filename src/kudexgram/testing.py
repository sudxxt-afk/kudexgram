from __future__ import annotations

from typing import Any

from kudexgram.client import TelegramClient


class FakeTelegramClient(TelegramClient):
    def __init__(self, *, updates: list[dict[str, Any]] | None = None) -> None:
        super().__init__("test-token")
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.updates = updates or []

    async def call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append((method, payload or {}))
        if method == "getUpdates":
            updates = self.updates
            self.updates = []
            return updates
        return {"ok": True}
