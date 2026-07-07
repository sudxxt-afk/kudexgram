from kudexgram import Bot, PollingRunner, PollingUpdateSource, Router
from kudexgram.testing import FakeTelegramClient


async def test_polling_source_decodes_updates_and_commits_offset() -> None:
    client = FakeTelegramClient(
        updates=[
            {
                "update_id": 10,
                "message": {
                    "message_id": 1,
                    "chat": {"id": 42, "type": "private"},
                    "text": "/start",
                },
            }
        ]
    )
    source = PollingUpdateSource(client)

    updates = await source.fetch()
    await source.commit(updates[0])

    assert updates[0].update_id == 10
    assert source.offset == 11


async def test_polling_runner_dispatches_fetched_updates() -> None:
    client = FakeTelegramClient(
        updates=[
            {
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "chat": {"id": 42, "type": "private"},
                    "text": "/start",
                },
            }
        ]
    )
    bot = Bot("token", client=client)
    router = Router()

    @router.command("start")
    async def start() -> str:
        return "hello"

    bot.include(router)
    runner = PollingRunner(bot.app, PollingUpdateSource(client))

    count = await runner.run_once()

    assert count == 1
    assert client.calls[-1] == ("sendMessage", {"chat_id": 42, "text": "hello"})
