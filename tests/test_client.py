import httpx
import pytest

from kudexgram import (
    TelegramAPIError,
    TelegramClient,
    TelegramHTTPError,
    TelegramNetworkError,
    TelegramRateLimitError,
)


def make_client(
    handler,
    *,
    retry_attempts: int = 3,
    sleeps: list[float] | None = None,
) -> TelegramClient:
    async def sleep(delay: float) -> None:
        if sleeps is not None:
            sleeps.append(delay)

    return TelegramClient(
        "token",
        http=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        retry_attempts=retry_attempts,
        retry_backoff=0.25,
        sleep=sleep,
    )


async def test_client_retries_http_5xx_then_succeeds() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(502, text="bad gateway")
        return httpx.Response(200, json={"ok": True, "result": {"done": True}})

    client = make_client(handler, sleeps=sleeps)

    result = await client.call("sendMessage", {"chat_id": 1, "text": "hi"})

    assert result == {"done": True}
    assert attempts == 2
    assert sleeps == [0.25]


async def test_client_retries_telegram_rate_limit_retry_after() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                429,
                json={
                    "ok": False,
                    "error_code": 429,
                    "description": "Too Many Requests",
                    "parameters": {"retry_after": 2},
                },
            )
        return httpx.Response(200, json={"ok": True, "result": True})

    client = make_client(handler, sleeps=sleeps)

    assert await client.call("answerCallbackQuery", {"callback_query_id": "cq-1"}) is True
    assert attempts == 2
    assert sleeps == [2.0]


async def test_client_raises_rate_limit_after_retry_budget() -> None:
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={
                "ok": False,
                "error_code": 429,
                "description": "Too Many Requests",
                "parameters": {"retry_after": 3},
            },
        )

    client = make_client(handler, retry_attempts=1, sleeps=sleeps)

    with pytest.raises(TelegramRateLimitError) as exc:
        await client.call("sendMessage", {"chat_id": 1, "text": "hi"})

    assert exc.value.retry_after == 3
    assert sleeps == [3.0]


async def test_client_does_not_retry_telegram_400_error() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            400,
            json={
                "ok": False,
                "error_code": 400,
                "description": "Bad Request: chat not found",
            },
        )

    client = make_client(handler)

    with pytest.raises(TelegramAPIError) as exc:
        await client.call("sendMessage", {"chat_id": 1, "text": "hi"})

    assert exc.value.error_code == 400
    assert attempts == 1


async def test_client_retries_network_errors_then_raises_readable_error() -> None:
    attempts = 0
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("timeout", request=request)

    client = make_client(handler, retry_attempts=2, sleeps=sleeps)

    with pytest.raises(TelegramNetworkError) as exc:
        await client.call("getUpdates")

    assert exc.value.method == "getUpdates"
    assert attempts == 3
    assert sleeps == [0.25, 0.5]


async def test_client_raises_http_error_for_non_json_4xx() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="forbidden")

    client = make_client(handler)

    with pytest.raises(TelegramHTTPError) as exc:
        await client.call("getMe")

    assert exc.value.status_code == 403
