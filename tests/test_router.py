import pytest

from kudexgram import Bot, CallbackQuery, Context, InlineKeyboard, Router, Update, User, ctx
from kudexgram.testing import FakeTelegramClient
from kudexgram.types import Chat, Message


def make_update(text: str) -> Update:
    return Update(
        update_id=1,
        message=Message(
            message_id=1,
            chat=Chat(id=42, type="private"),
            text=text,
        ),
    )


def make_callback_update(data: str, *, with_message: bool = True) -> Update:
    return Update(
        update_id=2,
        callback_query=CallbackQuery(
            id="cq-1",
            from_=User(id=7, is_bot=False, first_name="Ada", username="ada"),
            message=(
                Message(
                    message_id=9,
                    chat=Chat(id=42, type="private"),
                    text="Choose",
                )
                if with_message
                else None
            ),
            data=data,
        ),
    )


async def test_command_handler_replies() -> None:
    client = FakeTelegramClient()
    bot = Bot("token", client=client)
    router = Router()

    @router.command("start")
    async def start() -> None:
        await ctx.reply("hello")

    bot.include(router)

    handled = await bot.dispatch(make_update("/start"))

    assert handled is True
    assert client.calls == [("sendMessage", {"chat_id": 42, "text": "hello"})]


async def test_text_handler_receives_message_text() -> None:
    client = FakeTelegramClient()
    bot = Bot("token", client=client)
    router = Router()

    @router.text()
    async def echo(message: str) -> None:
        await ctx.reply(message)

    bot.include(router)

    handled = await bot.dispatch(make_update("ping"))

    assert handled is True
    assert client.calls == [("sendMessage", {"chat_id": 42, "text": "ping"})]


async def test_handler_can_receive_explicit_context_and_return_text() -> None:
    client = FakeTelegramClient()
    bot = Bot("token", client=client)
    router = Router()

    @router.command("start")
    async def start(context: Context) -> str:
        assert context.chat_id == 42
        return "hello from return"

    bot.include(router)

    handled = await bot.dispatch(make_update("/start"))

    assert handled is True
    assert client.calls == [("sendMessage", {"chat_id": 42, "text": "hello from return"})]


async def test_handler_can_receive_update() -> None:
    client = FakeTelegramClient()
    bot = Bot("token", client=client)
    router = Router()

    @router.text()
    async def echo(update: Update) -> str:
        assert update.message is not None
        return update.message.text or ""

    bot.include(router)

    handled = await bot.dispatch(make_update("typed update"))

    assert handled is True
    assert client.calls == [("sendMessage", {"chat_id": 42, "text": "typed update"})]


async def test_reply_markup_is_serialized_for_send_message() -> None:
    client = FakeTelegramClient()
    bot = Bot("token", client=client)
    router = Router()

    @router.command("start")
    async def start() -> None:
        await ctx.reply(
            "Choose",
            reply_markup=InlineKeyboard().button("Profile", callback="profile"),
        )

    bot.include(router)

    handled = await bot.dispatch(make_update("/start"))

    assert handled is True
    assert client.calls == [
        (
            "sendMessage",
            {
                "chat_id": 42,
                "text": "Choose",
                "reply_markup": {
                    "inline_keyboard": [[{"text": "Profile", "callback_data": "profile"}]]
                },
            },
        )
    ]


async def test_callback_handler_answers_and_replies_in_callback_chat() -> None:
    client = FakeTelegramClient()
    bot = Bot("token", client=client)
    router = Router()

    @router.callback("profile")
    async def profile(context: Context) -> str:
        assert context.callback_data == "profile"
        await context.answer_callback("Opening profile")
        return "Profile opened"

    bot.include(router)

    handled = await bot.dispatch(make_callback_update("profile"))

    assert handled is True
    assert client.calls == [
        ("answerCallbackQuery", {"callback_query_id": "cq-1", "text": "Opening profile"}),
        ("sendMessage", {"chat_id": 42, "text": "Profile opened"}),
    ]


async def test_callback_returned_text_requires_callback_message_chat() -> None:
    client = FakeTelegramClient()
    bot = Bot("token", client=client)
    router = Router()

    @router.callback("orphan")
    async def orphan() -> str:
        return "cannot send"

    bot.include(router)

    with pytest.raises(RuntimeError, match="Cannot reply to an update without a chat"):
        await bot.dispatch(make_callback_update("orphan", with_message=False))


def test_handler_signature_rejects_unknown_parameter() -> None:
    router = Router()

    with pytest.raises(TypeError, match="Unsupported handler parameter 'db'"):

        @router.command("start")
        async def start(db) -> str:
            return "never registered"


def test_handler_signature_rejects_unknown_annotated_parameter() -> None:
    router = Router()

    with pytest.raises(TypeError, match="Unsupported handler parameter 'db'"):

        @router.command("start")
        async def start(db: object) -> str:
            return "never registered"
