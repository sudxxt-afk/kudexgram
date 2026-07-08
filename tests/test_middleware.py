from kudexgram import Bot, Context
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


async def test_middleware_wraps_handler_dispatch() -> None:
    events: list[str] = []
    bot = Bot("token")

    @bot.use
    async def track(ctx: Context, next) -> bool:
        events.append(f"before:{ctx.chat_id}")
        handled = await next()
        events.append(f"after:{handled}")
        return handled

    @bot.command("start")
    async def start() -> str:
        events.append("handler")
        return "hello"

    scenario = bot.scenario(chat_id=42)

    await scenario.send_message("/start")

    assert events == ["before:42", "handler", "after:True"]
    scenario.assert_last_reply("hello")


async def test_middleware_can_short_circuit_dispatch() -> None:
    bot = Bot("token")

    @bot.use
    async def block(ctx: Context, next) -> bool:
        await ctx.reply("blocked")
        return True

    @bot.command("start")
    async def start() -> str:
        return "should not run"

    scenario = bot.scenario(chat_id=42)

    await scenario.send_message("/start")

    scenario.assert_last_reply("blocked")
    assert scenario.replies() == ["blocked"]


async def test_multiple_middlewares_run_in_registration_order() -> None:
    events: list[str] = []
    bot = Bot("token")

    @bot.use
    async def first(ctx: Context, next) -> bool:
        events.append("first:before")
        handled = await next()
        events.append("first:after")
        return handled

    @bot.use
    async def second(ctx: Context, next) -> bool:
        events.append("second:before")
        handled = await next()
        events.append("second:after")
        return handled

    @bot.text()
    async def echo(message: str) -> str:
        events.append("handler")
        return message

    await bot.scenario().send_message("ping")

    assert events == [
        "first:before",
        "second:before",
        "handler",
        "second:after",
        "first:after",
    ]
