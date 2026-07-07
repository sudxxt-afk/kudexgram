from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from kudexgram.client import TelegramClient
from kudexgram.types import Message, Update

_current_context: ContextVar[Context] = ContextVar("kudexgram_current_context")


class Context:
    def __init__(self, *, update: Update, client: TelegramClient) -> None:
        self.update = update
        self.client = client

    @property
    def message(self) -> Message | None:
        return self.update.message

    @property
    def chat_id(self) -> int | None:
        if self.message is None:
            return None
        return self.message.chat.id

    async def reply(self, text: str, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply to an update without a chat")
        return await self.client.send_message(self.chat_id, text, **params)


def get_current_context() -> Context:
    return _current_context.get()


class ContextProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_current_context(), name)


ctx = ContextProxy()
