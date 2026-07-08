import pytest
from kudexgram import (
    Bot,
    Context,
    InlineKeyboard,
    ReplyKeyboard,
    ReplyKeyboardRemove,
    TelegramClient,
)
from kudexgram.testing import FakeTelegramClient
from kudexgram.types import Chat, Message, Update, User


def test_reply_keyboard_to_dict() -> None:
    keyboard = ReplyKeyboard(resize_keyboard=True, one_time_keyboard=True, selective=True)
    keyboard.button("Btn 1").button("Btn 2").row().button("Btn 3")
    
    assert keyboard.to_dict() == {
        "keyboard": [
            ["Btn 1", "Btn 2"],
            ["Btn 3"],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True,
        "selective": True,
    }


def test_reply_keyboard_remove_to_dict() -> None:
    remove = ReplyKeyboardRemove(selective=True)
    assert remove.to_dict() == {
        "remove_keyboard": True,
        "selective": True,
    }


@pytest.mark.asyncio
async def test_client_api_coverage() -> None:
    client = FakeTelegramClient()
    
    await client.edit_message_text(chat_id=42, message_id=10, text="new text")
    assert client.calls[-1] == ("editMessageText", {"chat_id": 42, "message_id": 10, "text": "new text"})

    await client.edit_message_reply_markup(chat_id=42, message_id=10, reply_markup={"inline_keyboard": []})
    assert client.calls[-1] == ("editMessageReplyMarkup", {"chat_id": 42, "message_id": 10, "reply_markup": {"inline_keyboard": []}})

    await client.delete_message(chat_id=42, message_id=10)
    assert client.calls[-1] == ("deleteMessage", {"chat_id": 42, "message_id": 10})

    await client.send_photo(chat_id=42, photo="photo_url", caption="my photo")
    assert client.calls[-1] == ("sendPhoto", {"chat_id": 42, "photo": "photo_url", "caption": "my photo"})

    await client.send_document(chat_id=42, document="doc_url")
    assert client.calls[-1] == ("sendDocument", {"chat_id": 42, "document": "doc_url"})


@pytest.mark.asyncio
async def test_context_helpers_coverage() -> None:
    bot = Bot("token")
    client = FakeTelegramClient()
    bot.app.client = client

    @bot.command("start")
    async def start(ctx: Context) -> None:
        assert ctx.message_id == 123
        await ctx.edit_text("updated text")
        await ctx.delete_message()
        await ctx.reply_photo("photo_id", caption="pic")

    update = Update(
        update_id=1,
        message=Message(
            message_id=123,
            chat=Chat(id=42, type="private"),
            text="/start",
        ),
    )

    handled = await bot.dispatch(update)
    assert handled is True

    # Check the API calls made
    calls = client.calls
    assert ("editMessageText", {"chat_id": 42, "message_id": 123, "text": "updated text"}) in calls
    assert ("deleteMessage", {"chat_id": 42, "message_id": 123}) in calls
    assert ("sendPhoto", {"chat_id": 42, "photo": "photo_id", "caption": "pic"}) in calls
