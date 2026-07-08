from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import httpx


class TelegramAPIError(RuntimeError):
    def __init__(
        self,
        method: str,
        description: str,
        error_code: int | None = None,
        *,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.method = method
        self.description = description
        self.error_code = error_code
        self.parameters = parameters or {}
        super().__init__(f"Telegram API {method} failed: {description}")


class TelegramRateLimitError(TelegramAPIError):
    def __init__(
        self,
        method: str,
        description: str,
        *,
        retry_after: int,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(
            method=method,
            description=description,
            error_code=429,
            parameters=parameters,
        )


class TelegramNetworkError(RuntimeError):
    def __init__(self, method: str, cause: Exception) -> None:
        self.method = method
        self.cause = cause
        super().__init__(f"Telegram API {method} network error: {cause}")


class TelegramHTTPError(RuntimeError):
    def __init__(self, method: str, status_code: int, body: str) -> None:
        self.method = method
        self.status_code = status_code
        self.body = body
        super().__init__(f"Telegram API {method} HTTP {status_code}: {body}")


Sleep = Callable[[float], Awaitable[Any]]


class TelegramClient:
    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://api.telegram.org",
        http: httpx.AsyncClient | None = None,
        retry_attempts: int = 3,
        retry_backoff: float = 0.5,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self._http = http
        self._owns_http = http is None
        self.retry_attempts = retry_attempts
        self.retry_backoff = retry_backoff
        self._sleep = sleep

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/bot{self.token}"

    async def call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        normalized_payload = _normalize_payload(payload or {})
        for attempt in range(self.retry_attempts + 1):
            try:
                return await self._call_once(method, normalized_payload)
            except TelegramRateLimitError as error:
                if attempt >= self.retry_attempts:
                    raise
                await self._sleep(max(float(error.retry_after), 0.0))
            except TelegramHTTPError as error:
                if attempt >= self.retry_attempts or not _is_retryable_status(error.status_code):
                    raise
                await self._sleep(self._retry_delay(attempt))
            except TelegramAPIError as error:
                if (
                    attempt >= self.retry_attempts
                    or error.error_code is None
                    or not _is_retryable_status(error.error_code)
                ):
                    raise
                await self._sleep(self._retry_delay(attempt))
            except (httpx.TimeoutException, httpx.NetworkError) as error:
                if attempt >= self.retry_attempts:
                    raise TelegramNetworkError(method, error) from error
                await self._sleep(self._retry_delay(attempt))

        raise RuntimeError("unreachable Telegram retry state")

    async def _call_once(self, method: str, payload: dict[str, Any]) -> Any:
        response = await self.http.post(f"{self.api_url}/{method}", json=payload)
        data = _response_json(response)

        if response.status_code >= 400 and data is None:
            raise TelegramHTTPError(method, response.status_code, response.text)

        if response.status_code >= 400 and data is not None and data.get("ok") is not False:
            raise TelegramHTTPError(method, response.status_code, response.text)

        if data is None:
            return None

        if not data.get("ok", False):
            raise _telegram_error(method, data)

        return data.get("result")

    def _retry_delay(self, attempt: int) -> float:
        return self.retry_backoff * (2**attempt)

    async def get_updates(
        self,
        *,
        offset: int | None = None,
        long_poll_timeout: int = 30,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": long_poll_timeout, "limit": limit}
        if offset is not None:
            payload["offset"] = offset
        result = await self.call("getUpdates", payload)
        return list(result or [])

    async def send_message(self, chat_id: int | str, text: str, **params: Any) -> Any:
        payload = _normalize_payload({"chat_id": chat_id, "text": text, **params})
        return await self.call("sendMessage", payload)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        *,
        text: str | None = None,
        **params: Any,
    ) -> Any:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id, **params}
        if text is not None:
            payload["text"] = text
        return await self.call("answerCallbackQuery", _normalize_payload(payload))

    async def edit_message_text(
        self,
        chat_id: int | str | None = None,
        message_id: int | None = None,
        inline_message_id: str | None = None,
        *,
        text: str,
        **params: Any,
    ) -> Any:
        payload: dict[str, Any] = {"text": text, **params}
        if chat_id is not None:
            payload["chat_id"] = chat_id
        if message_id is not None:
            payload["message_id"] = message_id
        if inline_message_id is not None:
            payload["inline_message_id"] = inline_message_id
        return await self.call("editMessageText", payload)

    async def edit_message_reply_markup(
        self,
        chat_id: int | str | None = None,
        message_id: int | None = None,
        inline_message_id: str | None = None,
        *,
        reply_markup: Any | None = None,
        **params: Any,
    ) -> Any:
        payload: dict[str, Any] = {**params}
        if chat_id is not None:
            payload["chat_id"] = chat_id
        if message_id is not None:
            payload["message_id"] = message_id
        if inline_message_id is not None:
            payload["inline_message_id"] = inline_message_id
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return await self.call("editMessageReplyMarkup", payload)

    async def delete_message(self, chat_id: int | str, message_id: int) -> Any:
        return await self.call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    async def send_photo(self, chat_id: int | str, photo: str, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "photo": photo, **params}
        return await self.call("sendPhoto", payload)

    async def send_document(self, chat_id: int | str, document: str, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "document": document, **params}
        return await self.call("sendDocument", payload)

    async def get_me(self) -> Any:
        return await self.call("getMe")

    async def send_chat_action(self, chat_id: int | str, action: str, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "action": action, **params}
        return await self.call("sendChatAction", payload)

    async def send_audio(self, chat_id: int | str, audio: str, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "audio": audio, **params}
        return await self.call("sendAudio", payload)

    async def send_video(self, chat_id: int | str, video: str, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "video": video, **params}
        return await self.call("sendVideo", payload)

    async def send_voice(self, chat_id: int | str, voice: str, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "voice": voice, **params}
        return await self.call("sendVoice", payload)

    async def answer_pre_checkout_query(
        self,
        pre_checkout_query_id: str,
        ok: bool,
        *,
        error_message: str | None = None,
    ) -> Any:
        payload: dict[str, Any] = {"pre_checkout_query_id": pre_checkout_query_id, "ok": ok}
        if error_message is not None:
            payload["error_message"] = error_message
        return await self.call("answerPreCheckoutQuery", payload)

    async def set_webhook(self, url: str, **params: Any) -> Any:
        payload = {"url": url, **params}
        return await self.call("setWebhook", payload)

    async def delete_webhook(self, drop_pending_updates: bool | None = None, **params: Any) -> Any:
        payload = {**params}
        if drop_pending_updates is not None:
            payload["drop_pending_updates"] = drop_pending_updates
        return await self.call("deleteWebhook", payload)

    async def get_webhook_info(self) -> Any:
        return await self.call("getWebhookInfo")

    async def ban_chat_member(self, chat_id: int | str, user_id: int, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "user_id": user_id, **params}
        return await self.call("banChatMember", payload)

    async def unban_chat_member(self, chat_id: int | str, user_id: int, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "user_id": user_id, **params}
        return await self.call("unbanChatMember", payload)

    async def restrict_chat_member(self, chat_id: int | str, user_id: int, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "user_id": user_id, **params}
        return await self.call("restrictChatMember", payload)

    async def get_chat(self, chat_id: int | str) -> Any:
        return await self.call("getChat", {"chat_id": chat_id})

    async def get_chat_member(self, chat_id: int | str, user_id: int) -> Any:
        return await self.call("getChatMember", {"chat_id": chat_id, "user_id": user_id})

    async def send_location(
        self,
        chat_id: int | str,
        latitude: float,
        longitude: float,
        **params: Any,
    ) -> Any:
        payload = {"chat_id": chat_id, "latitude": latitude, "longitude": longitude, **params}
        return await self.call("sendLocation", payload)

    async def send_poll(
        self,
        chat_id: int | str,
        question: str,
        options: list[str],
        **params: Any,
    ) -> Any:
        payload = {"chat_id": chat_id, "question": question, "options": options, **params}
        return await self.call("sendPoll", payload)

    async def stop_poll(self, chat_id: int | str, message_id: int, **params: Any) -> Any:
        payload = {"chat_id": chat_id, "message_id": message_id, **params}
        return await self.call("stopPoll", payload)

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None:
            timeout = httpx.Timeout(35.0, connect=10.0)
            self._http = httpx.AsyncClient(timeout=timeout)
        return self._http

    async def aclose(self) -> None:
        if self._owns_http and self._http is not None:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self) -> TelegramClient:
        _ = self.http
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: _normalize_value(value) for key, value in payload.items()}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return _normalize_value(to_dict())
    return value


def _response_json(response: httpx.Response) -> dict[str, Any] | None:
    try:
        data = response.json()
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _telegram_error(method: str, data: dict[str, Any]) -> TelegramAPIError:
    description = str(data.get("description", "unknown Telegram API error"))
    error_code = data.get("error_code")
    parameters = data.get("parameters")
    if not isinstance(parameters, dict):
        parameters = {}

    if error_code == 429:
        retry_after = parameters.get("retry_after", 1)
        return TelegramRateLimitError(
            method=method,
            description=description,
            retry_after=int(retry_after),
            parameters=parameters,
        )

    return TelegramAPIError(
        method=method,
        description=description,
        error_code=error_code if isinstance(error_code, int) else None,
        parameters=parameters,
    )


def _is_retryable_status(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code <= 599
