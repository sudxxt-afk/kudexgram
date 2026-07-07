from __future__ import annotations

from typing import Any

import msgspec


class User(msgspec.Struct, frozen=True):
    id: int
    is_bot: bool
    first_name: str
    username: str | None = None


class Chat(msgspec.Struct, frozen=True):
    id: int
    type: str
    title: str | None = None
    username: str | None = None
    first_name: str | None = None


class Message(msgspec.Struct, frozen=True):
    message_id: int
    chat: Chat
    date: int | None = None
    text: str | None = None
    from_: User | None = msgspec.field(default=None, name="from")


class Update(msgspec.Struct, frozen=True):
    update_id: int
    message: Message | None = None


def convert_update(value: dict[str, Any]) -> Update:
    return msgspec.convert(value, Update)

