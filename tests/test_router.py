from kudexgram import Bot, Context, Router, Update, ctx
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
