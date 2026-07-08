from kudexgram import Bot, Context, InlineKeyboard
from kudexgram.testing import FakeTelegramClient
from kudexgram.types import Chat, Message, Update


def make_update(text: str) -> Update:
    return Update(
        update_id=1,
        message=Message(
            message_id=1,
            chat=Chat(id=42, type="private"),
            text=text,
        ),
    )


async def test_bot_command_shortcut_registers_handler() -> None:
    client = FakeTelegramClient()
    bot = Bot("token", client=client)

    @bot.command("start")
    async def start() -> str:
        return "hello"

    handled = await bot.dispatch(make_update("/start"))

    assert handled is True
    assert client.calls == [("sendMessage", {"chat_id": 42, "text": "hello"})]


async def test_bot_text_shortcut_registers_handler() -> None:
    client = FakeTelegramClient()
    bot = Bot("token", client=client)

    @bot.text()
    async def echo(message: str) -> str:
        return message

    handled = await bot.dispatch(make_update("ping"))

    assert handled is True
    assert client.calls == [("sendMessage", {"chat_id": 42, "text": "ping"})]


async def test_bot_callback_shortcut_registers_handler() -> None:
    bot = Bot("token")

    @bot.command("start")
    async def start(ctx: Context) -> None:
        await ctx.reply(
            "choose",
            reply_markup=InlineKeyboard().button("Profile", callback="profile"),
        )

    @bot.callback("profile")
    async def profile(ctx: Context) -> str:
        await ctx.answer_callback("ok")
        return "profile"

    scenario = bot.scenario(chat_id=42)

    await scenario.tap("profile")

    scenario.assert_callback_answered("ok")
    scenario.assert_last_reply("profile")
