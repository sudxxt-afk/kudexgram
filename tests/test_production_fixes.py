import io
import pytest
from pathlib import Path
from kudexgram import (
    Bot,
    Context,
    KudexgramContextError,
    Router,
    ctx,
)
from kudexgram.client import _prepare_multipart
from kudexgram.testing import FakeTelegramClient
from kudexgram.types import Chat, Message, Update


def test_prepare_multipart_detects_files() -> None:
    file_like = io.BytesIO(b"hello world")
    setattr(file_like, "name", "test_file.txt")
    
    payload = {
        "chat_id": 123,
        "photo": file_like,
        "caption": "test caption",
        "reply_markup": {"inline_keyboard": []}
    }
    
    form_data, files = _prepare_multipart(payload)
    
    assert files["photo"] == ("test_file.txt", file_like)
    assert form_data["chat_id"] == "123"
    assert form_data["caption"] == "test caption"
    assert form_data["reply_markup"] == '{"inline_keyboard": []}'


@pytest.mark.asyncio
async def test_polling_runner_catches_handler_error_and_commits(tmp_path) -> None:
    bot = Bot("token")
    client = FakeTelegramClient()
    bot.app.client = client
    
    # Track commits in fake client
    committed_offset = None
    
    # Mock source to track commits
    class FakeSource:
        async def fetch(self) -> list[Update]:
            return [
                Update(
                    update_id=42,
                    message=Message(
                        message_id=1,
                        chat=Chat(id=1, type="private"),
                        text="/start",
                    ),
                )
            ]
        
        async def commit(self, update: Update) -> None:
            nonlocal committed_offset
            committed_offset = update.update_id

    @bot.command("start")
    async def start(ctx: Context) -> None:
        raise ValueError("Simulated handler database error")

    from kudexgram.runtime import PollingRunner
    runner = PollingRunner(bot.app, FakeSource())
    
    # Verify that run_once does not propagate ValueError
    count = await runner.run_once()
    assert count == 1
    
    # Check that commit was still called for offset 42
    assert committed_offset == 42


@pytest.mark.asyncio
async def test_download_file_streams_to_disk(tmp_path) -> None:
    client = FakeTelegramClient()
    dest = tmp_path / "downloaded.jpg"
    
    # download_file on FakeTelegramClient returns mock data
    await client.download_file("path/to/file", destination=dest)
    
    # The fake client mock will record the call
    assert client.calls[-1] == ("downloadFile", {"file_path": "path/to/file"})


@pytest.mark.asyncio
async def test_relaxed_handler_parameter_names() -> None:
    bot = Bot("token")
    client = FakeTelegramClient()
    bot.app.client = client
    
    @bot.text()
    async def echo(text: str, msg: str, ctx: Context) -> None:
        assert text == "hello"
        assert msg == "hello"
        await ctx.reply(f"echo: {text}")

    update = Update(
        update_id=1,
        message=Message(
            message_id=1,
            chat=Chat(id=42, type="private"),
            text="hello",
        ),
    )
    
    handled = await bot.dispatch(update)
    assert handled is True
    assert client.calls[-1] == ("sendMessage", {"chat_id": 42, "text": "echo: hello"})


def test_ctx_outside_context_raises_friendly_error() -> None:
    with pytest.raises(KudexgramContextError) as exc_info:
        _ = ctx.chat_id
        
    assert "Working outside of request context" in str(exc_info.value)
