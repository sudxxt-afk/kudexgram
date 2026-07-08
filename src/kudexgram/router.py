from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from kudexgram.context import Context
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

    async def dispatch(self, context: Context) -> bool:
        for route in self.routes:
            if not route.filter(context.update):
                continue

            result = await route.resolver.call(context)
            await _render_result(context, result)
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
    name = parameter.name
    if annotation is Context:
        return ArgumentSource.CONTEXT
    if annotation is Update:
        return ArgumentSource.UPDATE
    if annotation is Message:
        return ArgumentSource.MESSAGE
    if annotation is CallbackQuery:
        return ArgumentSource.CALLBACK_QUERY
    if annotation is str and name == "message":
        return ArgumentSource.MESSAGE_TEXT
    if annotation is str and name == "callback_data":
        return ArgumentSource.CALLBACK_DATA
    if name in {"ctx", "context"}:
        return ArgumentSource.CONTEXT
    if name == "update":
        return ArgumentSource.UPDATE
    if name == "message":
        return ArgumentSource.MESSAGE_TEXT
    if name == "callback_query":
        return ArgumentSource.CALLBACK_QUERY
    if name == "callback_data":
        return ArgumentSource.CALLBACK_DATA
    annotation_hint = ""
    if annotation is not inspect.Signature.empty:
        annotation_hint = f" with annotation {annotation!r}"
    raise TypeError(
        f"Unsupported handler parameter {name!r}{annotation_hint}. "
        "Use ctx: Context, update: Update, message: str, "
        "callback_query: CallbackQuery, or callback_data: str."
    )


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
