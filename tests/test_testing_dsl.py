from kudexgram import Bot, Context, InlineKeyboard, Router


def make_bot() -> Bot:
    bot = Bot("token")
    router = Router()

    @router.command("start")
    async def start(ctx: Context) -> None:
        user = ctx.message.from_.first_name if ctx.message and ctx.message.from_ else "there"
        await ctx.reply(
            f"Hey {user}",
            reply_markup=InlineKeyboard().button("Profile", callback="profile"),
        )

    @router.callback("profile")
    async def profile(ctx: Context) -> None:
        await ctx.answer_callback("Opening profile")
        await ctx.reply("Profile tapped")

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
    scenario.assert_api_called(
        "sendMessage",
        {
            "chat_id": 42,
            "text": "Hey Ada",
            "reply_markup": {
                "inline_keyboard": [[{"text": "Profile", "callback_data": "profile"}]]
            },
        },
    )


async def test_scenario_alias_send_and_api_assertion() -> None:
    bot = make_bot()
    scenario = bot.scenario(chat_id=42)

    await scenario.send("ping")

    scenario.assert_last_reply("Echo: ping")
    scenario.assert_api_called("sendMessage", {"chat_id": 42, "text": "Echo: ping"})


async def test_scenario_tap_dispatches_callback_query() -> None:
    bot = make_bot()
    scenario = bot.scenario(chat_id=42)

    await scenario.tap("profile")

    scenario.assert_handled()
    scenario.assert_callback_answered("Opening profile")
    scenario.assert_last_reply("Profile tapped")
