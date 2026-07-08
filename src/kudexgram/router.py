from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from kudexgram.client import TelegramClient
from kudexgram.context import Context, _current_context
from kudexgram.types import CallbackQuery, Message, Update

Handler = Callable[..., Awaitable[Any]]
Filter = Callable[[Update], bool]


@dataclass(frozen=True)
class Route:
    filter: Filter
    handler: Handler
    resolver: HandlerResolver


class Router:
    def __init__(self) -> None:
        self.routes: list[Route] = []

    def command(self, name: str) -> Callable[[Handler], Handler]:
        command_name = name.removeprefix("/")

        def decorator(handler: Handler) -> Handler:
            self.routes.append(
                Route(
                    filter=lambda update: _is_command(update, command_name),
                    handler=handler,
                    resolver=HandlerResolver.compile(handler),
                )
            )
            return handler

        return decorator

    def text(self) -> Callable[[Handler], Handler]:
        def decorator(handler: Handler) -> Handler:
            self.routes.append(
                Route(
                    filter=_has_text,
                    handler=handler,
                    resolver=HandlerResolver.compile(handler),
                )
            )
            return handler

        return decorator

    def callback(self, data: str) -> Callable[[Handler], Handler]:
        def decorator(handler: Handler) -> Handler:
            self.routes.append(
                Route(
                    filter=lambda update: _has_callback_data(update, data),
                    handler=handler,
                    resolver=HandlerResolver.compile(handler),
                )
            )
            return handler

        return decorator

    async def dispatch(self, update: Update, client: TelegramClient) -> bool:
        for route in self.routes:
            if not route.filter(update):
                continue

            context = Context(update=update, client=client)
            token = _current_context.set(context)
            try:
                result = await route.resolver.call(context)
                await _render_result(context, result)
            finally:
                _current_context.reset(token)
            return True

        return False


class ArgumentSource(Enum):
    CONTEXT = "context"
    UPDATE = "update"
    MESSAGE = "message"
    MESSAGE_TEXT = "message_text"
    CALLBACK_QUERY = "callback_query"
    CALLBACK_DATA = "callback_data"


@dataclass(frozen=True)
class HandlerResolver:
    handler: Handler
    arguments: tuple[ArgumentSource, ...]

    @classmethod
    def compile(cls, handler: Handler) -> HandlerResolver:
        signature = inspect.signature(handler)
        arguments = tuple(
            _resolve_argument(parameter) for parameter in signature.parameters.values()
        )
        return cls(handler=handler, arguments=arguments)

    async def call(self, context: Context) -> Any:
        values = [_read_argument(source, context) for source in self.arguments]
        return await self.handler(*values)


async def _render_result(context: Context, result: Any) -> None:
    if isinstance(result, str):
        await context.reply(result)


def _resolve_argument(parameter: inspect.Parameter) -> ArgumentSource:
    annotation = parameter.annotation
    if annotation is Context:
        return ArgumentSource.CONTEXT
    if annotation is Update:
        return ArgumentSource.UPDATE
    if annotation is Message:
        return ArgumentSource.MESSAGE
    if annotation is CallbackQuery:
        return ArgumentSource.CALLBACK_QUERY
    if annotation is str and parameter.name == "message":
        return ArgumentSource.MESSAGE_TEXT
    if annotation is str and parameter.name == "callback_data":
        return ArgumentSource.CALLBACK_DATA
    if parameter.name == "ctx":
        return ArgumentSource.CONTEXT
    if parameter.name == "update":
        return ArgumentSource.UPDATE
    if parameter.name == "message":
        return ArgumentSource.MESSAGE_TEXT
    if parameter.name == "callback_query":
        return ArgumentSource.CALLBACK_QUERY
    if parameter.name == "callback_data":
        return ArgumentSource.CALLBACK_DATA
    return ArgumentSource.CONTEXT


def _read_argument(source: ArgumentSource, context: Context) -> Any:
    if source is ArgumentSource.CONTEXT:
        return context
    if source is ArgumentSource.UPDATE:
        return context.update
    if source is ArgumentSource.MESSAGE:
        return context.message
    if source is ArgumentSource.MESSAGE_TEXT:
        return context.message.text if context.message else None
    if source is ArgumentSource.CALLBACK_QUERY:
        return context.callback_query
    if source is ArgumentSource.CALLBACK_DATA:
        return context.callback_data
    raise RuntimeError(f"Unknown handler argument source: {source}")


def _has_text(update: Update) -> bool:
    return bool(update.message and update.message.text)


def _is_command(update: Update, command_name: str) -> bool:
    if not update.message or not update.message.text:
        return False
    head = update.message.text.split(maxsplit=1)[0]
    return head == f"/{command_name}" or head.startswith(f"/{command_name}@")


def _has_callback_data(update: Update, data: str) -> bool:
    return bool(update.callback_query and update.callback_query.data == data)
