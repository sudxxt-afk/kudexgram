from __future__ import annotations

from typing import Any

import httpx


class TelegramAPIError(RuntimeError):
    def __init__(self, method: str, description: str, error_code: int | None = None) -> None:
        self.method = method
        self.description = description
        self.error_code = error_code
        super().__init__(f"Telegram API {method} failed: {description}")


class TelegramClient:
    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://api.telegram.org",
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self._http = http
        self._owns_http = http is None

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/bot{self.token}"

    async def call(self, method: str, payload: dict[str, Any] | None = None) -> Any:
        response = await self.http.post(f"{self.api_url}/{method}", json=payload or {})
        response.raise_for_status()
        data = response.json()

        if not data.get("ok", False):
            raise TelegramAPIError(
                method=method,
                description=data.get("description", "unknown Telegram API error"),
                error_code=data.get("error_code"),
            )

        return data.get("result")

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
        return await self.call("sendMessage", {"chat_id": chat_id, "text": text, **params})

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
