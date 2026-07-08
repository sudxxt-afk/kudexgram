from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from kudexgram.client import TelegramClient
from kudexgram.types import CallbackQuery, Message, Update

_current_context: ContextVar[Context] = ContextVar("kudexgram_current_context")


class Context:
    def __init__(self, *, update: Update, client: TelegramClient) -> None:
        self.update = update
        self.client = client

    @property
    def message(self) -> Message | None:
        if self.update.message is not None:
            return self.update.message
        if self.callback_query is not None:
            return self.callback_query.message
        return None

    @property
    def callback_query(self) -> CallbackQuery | None:
        return self.update.callback_query

    @property
    def callback_data(self) -> str | None:
        if self.callback_query is None:
            return None
        return self.callback_query.data

    @property
    def chat_id(self) -> int | None:
        if self.message is None:
            return None
        return self.message.chat.id

    async def reply(self, text: str, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply to an update without a chat")
        return await self.client.send_message(self.chat_id, text, **params)

    async def answer_callback(self, text: str | None = None, **params: Any) -> Any:
        if self.callback_query is None:
            raise RuntimeError("Cannot answer callback query outside of a callback update")
        return await self.client.answer_callback_query(
            self.callback_query.id,
            text=text,
            **params,
        )

    @property
    def message_id(self) -> int | None:
        if self.message is None:
            return None
        return self.message.message_id

    async def edit_text(self, text: str, **params: Any) -> Any:
        if self.chat_id is None or self.message_id is None:
            raise RuntimeError("Cannot edit message text without chat_id and message_id")
        return await self.client.edit_message_text(
            chat_id=self.chat_id,
            message_id=self.message_id,
            text=text,
            **params,
        )

    async def delete_message(self) -> Any:
        if self.chat_id is None or self.message_id is None:
            raise RuntimeError("Cannot delete message without chat_id and message_id")
        return await self.client.delete_message(self.chat_id, self.message_id)

    async def reply_photo(self, photo: str, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply with photo to an update without a chat")
        return await self.client.send_photo(self.chat_id, photo, **params)

    async def send_action(self, action: str, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot send chat action to an update without a chat")
        return await self.client.send_chat_action(self.chat_id, action, **params)

    async def reply_audio(self, audio: str, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply with audio to an update without a chat")
        return await self.client.send_audio(self.chat_id, audio, **params)

    async def reply_video(self, video: str, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply with video to an update without a chat")
        return await self.client.send_video(self.chat_id, video, **params)

    async def reply_voice(self, voice: str, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply with voice to an update without a chat")
        return await self.client.send_voice(self.chat_id, voice, **params)

    async def reply_location(self, latitude: float, longitude: float, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply with location to an update without a chat")
        return await self.client.send_location(self.chat_id, latitude, longitude, **params)

    async def reply_poll(self, question: str, options: list[str], **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply with poll to an update without a chat")
        return await self.client.send_poll(self.chat_id, question, options, **params)

    async def ban_member(self, user_id: int, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot ban chat member without a chat")
        return await self.client.ban_chat_member(self.chat_id, user_id, **params)

    async def unban_member(self, user_id: int, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot unban chat member without a chat")
        return await self.client.unban_chat_member(self.chat_id, user_id, **params)

    async def reply_sticker(self, sticker: str, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply with sticker to an update without a chat")
        return await self.client.send_sticker(self.chat_id, sticker, **params)

    async def reply_dice(self, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply with dice to an update without a chat")
        return await self.client.send_dice(self.chat_id, **params)

    async def reply_animation(self, animation: str, **params: Any) -> Any:
        if self.chat_id is None:
            raise RuntimeError("Cannot reply with animation to an update without a chat")
        return await self.client.send_animation(self.chat_id, animation, **params)


def get_current_context() -> Context:
    return _current_context.get()


class ContextProxy:
    def __getattr__(self, name: str) -> Any:
        return getattr(get_current_context(), name)


ctx = ContextProxy()
