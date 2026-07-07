from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol


@dataclass(frozen=True)
class StateRecord:
    value: dict[str, Any]
    version: int = 1
    expires_at: datetime | None = None


class StateStore(Protocol):
    async def load(self, key: str) -> StateRecord | None: ...
    async def save(
        self,
        key: str,
        value: dict[str, Any],
        *,
        ttl_seconds: int | None = None,
    ) -> None: ...

    async def delete(self, key: str) -> None: ...
    async def touch(self, key: str, *, ttl_seconds: int) -> None: ...


class MemoryStateStore:
    def __init__(self, initial: MutableMapping[str, StateRecord] | None = None) -> None:
        self._data = initial or {}

    async def load(self, key: str) -> StateRecord | None:
        record = self._data.get(key)
        if record is None:
            return None
        if record.expires_at is not None and record.expires_at <= datetime.now():
            await self.delete(key)
            return None
        return StateRecord(
            value=dict(record.value),
            version=record.version,
            expires_at=record.expires_at,
        )

    async def save(
        self,
        key: str,
        value: dict[str, Any],
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        previous = await self.load(key)
        expires_at = None
        if ttl_seconds is not None:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        version = 1 if previous is None else previous.version + 1
        self._data[key] = StateRecord(value=dict(value), version=version, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def touch(self, key: str, *, ttl_seconds: int) -> None:
        record = await self.load(key)
        if record is None:
            return
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        self._data[key] = StateRecord(
            value=record.value,
            version=record.version + 1,
            expires_at=expires_at,
        )

    async def get(self, key: str) -> dict[str, Any] | None:
        record = await self.load(key)
        return record.value if record is not None else None

    async def set(self, key: str, value: dict[str, Any]) -> None:
        await self.save(key, value)

    async def clear(self, key: str) -> None:
        await self.delete(key)
