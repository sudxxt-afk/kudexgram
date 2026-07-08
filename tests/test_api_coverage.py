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

    await client.get_me()
    assert client.calls[-1] == ("getMe", {})

    await client.send_chat_action(chat_id=42, action="typing")
    assert client.calls[-1] == ("sendChatAction", {"chat_id": 42, "action": "typing"})

    await client.send_audio(chat_id=42, audio="audio_url")
    assert client.calls[-1] == ("sendAudio", {"chat_id": 42, "audio": "audio_url"})

    await client.send_video(chat_id=42, video="video_url")
    assert client.calls[-1] == ("sendVideo", {"chat_id": 42, "video": "video_url"})

    await client.send_voice(chat_id=42, voice="voice_url")
    assert client.calls[-1] == ("sendVoice", {"chat_id": 42, "voice": "voice_url"})

    await client.answer_pre_checkout_query(pre_checkout_query_id="pq-123", ok=True, error_message="error")
    assert client.calls[-1] == ("answerPreCheckoutQuery", {"pre_checkout_query_id": "pq-123", "ok": True, "error_message": "error"})

    await client.set_webhook(url="https://example.com/webhook", max_connections=40)
    assert client.calls[-1] == ("setWebhook", {"url": "https://example.com/webhook", "max_connections": 40})

    await client.delete_webhook(drop_pending_updates=True)
    assert client.calls[-1] == ("deleteWebhook", {"drop_pending_updates": True})

    await client.get_webhook_info()
    assert client.calls[-1] == ("getWebhookInfo", {})

    await client.ban_chat_member(chat_id=42, user_id=99)
    assert client.calls[-1] == ("banChatMember", {"chat_id": 42, "user_id": 99})

    await client.unban_chat_member(chat_id=42, user_id=99)
    assert client.calls[-1] == ("unbanChatMember", {"chat_id": 42, "user_id": 99})

    await client.restrict_chat_member(chat_id=42, user_id=99, permissions={})
    assert client.calls[-1] == ("restrictChatMember", {"chat_id": 42, "user_id": 99, "permissions": {}})

    await client.get_chat(chat_id=42)
    assert client.calls[-1] == ("getChat", {"chat_id": 42})

    await client.get_chat_member(chat_id=42, user_id=99)
    assert client.calls[-1] == ("getChatMember", {"chat_id": 42, "user_id": 99})

    await client.send_location(chat_id=42, latitude=55.75, longitude=37.61)
    assert client.calls[-1] == ("sendLocation", {"chat_id": 42, "latitude": 55.75, "longitude": 37.61})

    await client.send_poll(chat_id=42, question="Q?", options=["A", "B"])
    assert client.calls[-1] == ("sendPoll", {"chat_id": 42, "question": "Q?", "options": ["A", "B"]})

    await client.stop_poll(chat_id=42, message_id=10)
    assert client.calls[-1] == ("stopPoll", {"chat_id": 42, "message_id": 10})

    await client.get_file(file_id="file-123")
    assert client.calls[-1] == ("getFile", {"file_id": "file-123"})

    await client.answer_inline_query(inline_query_id="iq-123", results=[])
    assert client.calls[-1] == ("answerInlineQuery", {"inline_query_id": "iq-123", "results": []})

    await client.set_my_commands(commands=[])
    assert client.calls[-1] == ("setMyCommands", {"commands": []})

    await client.delete_my_commands()
    assert client.calls[-1] == ("deleteMyCommands", {})

    await client.get_my_commands()
    assert client.calls[-1] == ("getMyCommands", {})

    await client.get_user_profile_photos(user_id=99)
    assert client.calls[-1] == ("getUserProfilePhotos", {"user_id": 99})

    await client.send_sticker(chat_id=42, sticker="sticker-id")
    assert client.calls[-1] == ("sendSticker", {"chat_id": 42, "sticker": "sticker-id"})

    await client.send_dice(chat_id=42)
    assert client.calls[-1] == ("sendDice", {"chat_id": 42})

    await client.send_animation(chat_id=42, animation="anim-id")
    assert client.calls[-1] == ("sendAnimation", {"chat_id": 42, "animation": "anim-id"})


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
        await ctx.send_action("typing")
        await ctx.reply_audio("audio_id")
        await ctx.reply_video("video_id")
        await ctx.reply_voice("voice_id")
        await ctx.reply_location(55.75, 37.61)
        await ctx.reply_poll("Q?", ["A", "B"])
        await ctx.ban_member(99)
        await ctx.unban_member(99)
        await ctx.reply_sticker("sticker-id")
        await ctx.reply_dice()
        await ctx.reply_animation("anim-id")

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
    assert ("sendChatAction", {"chat_id": 42, "action": "typing"}) in calls
    assert ("sendAudio", {"chat_id": 42, "audio": "audio_id"}) in calls
    assert ("sendVideo", {"chat_id": 42, "video": "video_id"}) in calls
    assert ("sendVoice", {"chat_id": 42, "voice": "voice_id"}) in calls
    assert ("sendLocation", {"chat_id": 42, "latitude": 55.75, "longitude": 37.61}) in calls
    assert ("sendPoll", {"chat_id": 42, "question": "Q?", "options": ["A", "B"]}) in calls
    assert ("banChatMember", {"chat_id": 42, "user_id": 99}) in calls
    assert ("unbanChatMember", {"chat_id": 42, "user_id": 99}) in calls
    assert ("sendSticker", {"chat_id": 42, "sticker": "sticker-id"}) in calls
    assert ("sendDice", {"chat_id": 42}) in calls
    assert ("sendAnimation", {"chat_id": 42, "animation": "anim-id"}) in calls
