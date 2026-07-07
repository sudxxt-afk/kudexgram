from kudexgram import Bot, Context, Router


def make_bot() -> Bot:
    bot = Bot("token")
    router = Router()

    @router.command("start")
    async def start(ctx: Context) -> str:
        user = ctx.message.from_.first_name if ctx.message and ctx.message.from_ else "there"
        return f"Hey {user}"

    @router.text()
    async def echo(message: str) -> str:
        return f"Echo: {message}"

    bot.include(router)
    return bot


async def test_scenario_sends_message_and_asserts_reply() -> None:
    bot = make_bot()
    scenario = bot.scenario(chat_id=42, user_id=7, first_name="Ada")

    await scenario.send_message("/start")

    scenario.assert_handled()
    scenario.assert_replied("Hey Ada")
    scenario.assert_last_reply("Hey Ada")


async def test_scenario_alias_send_and_api_assertion() -> None:
    bot = make_bot()
    scenario = bot.scenario(chat_id=42)

    await scenario.send("ping")

    scenario.assert_last_reply("Echo: ping")
    scenario.assert_api_called("sendMessage", {"chat_id": 42, "text": "Echo: ping"})
