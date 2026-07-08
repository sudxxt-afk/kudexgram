from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kudexgram.bot import Bot
from kudexgram.client import TelegramClient
from kudexgram.types import CallbackQuery, Chat, Message, Update, User


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

    def sent_messages(self) -> list[dict[str, Any]]:
        return [payload for method, payload in self.calls if method == "sendMessage"]

    def answered_callbacks(self) -> list[dict[str, Any]]:
        return [payload for method, payload in self.calls if method == "answerCallbackQuery"]


@dataclass(frozen=True)
class ScenarioUser:
    id: int = 1
    first_name: str = "Test"
    username: str | None = "test_user"
    is_bot: bool = False


@dataclass(frozen=True)
class ScenarioChat:
    id: int = 1
    type: str = "private"


class BotScenario:
    def __init__(
        self,
        bot: Bot,
        *,
        chat_id: int = 1,
        user_id: int = 1,
        first_name: str = "Test",
        username: str | None = "test_user",
    ) -> None:
        self.bot = bot
        self.client = FakeTelegramClient()
        self.bot.app.client = self.client
        self.chat = ScenarioChat(id=chat_id)
        self.user = ScenarioUser(id=user_id, first_name=first_name, username=username)
        self._next_update_id = 1
        self._next_message_id = 1
        self.handled: list[bool] = []

    async def send_message(self, text: str) -> bool:
        update = self.make_message_update(text)
        handled = await self.bot.dispatch(update)
        self.handled.append(handled)
        return handled

    async def send(self, text: str) -> bool:
        return await self.send_message(text)

    async def tap(self, callback_data: str) -> bool:
        update = self.make_callback_update(callback_data)
        handled = await self.bot.dispatch(update)
        self.handled.append(handled)
        return handled

    def make_message_update(self, text: str) -> Update:
        update = Update(
            update_id=self._next_update_id,
            message=Message(
                message_id=self._next_message_id,
                chat=Chat(id=self.chat.id, type=self.chat.type),
                text=text,
                from_=User(
                    id=self.user.id,
                    is_bot=self.user.is_bot,
                    first_name=self.user.first_name,
                    username=self.user.username,
                ),
            ),
        )
        self._next_update_id += 1
        self._next_message_id += 1
        return update

    def make_callback_update(self, callback_data: str) -> Update:
        callback_message = Message(
            message_id=self._next_message_id,
            chat=Chat(id=self.chat.id, type=self.chat.type),
            text=self._last_sent_message_text(),
        )
        update = Update(
            update_id=self._next_update_id,
            callback_query=CallbackQuery(
                id=f"cq-{self._next_update_id}",
                from_=User(
                    id=self.user.id,
                    is_bot=self.user.is_bot,
                    first_name=self.user.first_name,
                    username=self.user.username,
                ),
                message=callback_message,
                data=callback_data,
            ),
        )
        self._next_update_id += 1
        self._next_message_id += 1
        return update

    def replies(self) -> list[str]:
        return [
            str(message["text"])
            for message in self.client.sent_messages()
            if "text" in message
        ]

    def assert_replied(self, text: str) -> None:
        replies = self.replies()
        if text not in replies:
            raise AssertionError(f"Expected bot to reply {text!r}, got {replies!r}")

    def assert_last_reply(self, text: str) -> None:
        replies = self.replies()
        if not replies:
            raise AssertionError("Expected bot to reply, but no messages were sent")
        if replies[-1] != text:
            raise AssertionError(f"Expected last reply {text!r}, got {replies[-1]!r}")

    def assert_api_called(self, method: str, payload: dict[str, Any] | None = None) -> None:
        expected_calls = [
            call
            for call in self.client.calls
            if call[0] == method and (payload is None or call[1] == payload)
        ]
        if not expected_calls:
            raise AssertionError(
                f"Expected API call {method!r} with payload {payload!r}, "
                f"got {self.client.calls!r}"
            )

    def assert_handled(self) -> None:
        if not self.handled or not self.handled[-1]:
            raise AssertionError(f"Expected last update to be handled, got {self.handled!r}")

    def assert_callback_answered(self, text: str | None = None) -> None:
        answers = self.client.answered_callbacks()
        if not answers:
            raise AssertionError("Expected bot to answer a callback query, but none were sent")
        if text is None:
            return
        actual = [answer.get("text") for answer in answers]
        if text not in actual:
            raise AssertionError(f"Expected callback answer {text!r}, got {actual!r}")

    def _last_sent_message_text(self) -> str | None:
        sent_messages = self.client.sent_messages()
        if not sent_messages:
            return None
        value = sent_messages[-1].get("text")
        return str(value) if value is not None else None
