# Kudexgram

**Kudexgram is a Python framework for production Telegram bots.**

It is currently **pre-alpha**. The goal is not to be one more Bot API wrapper, but a
FastAPI-like toolkit for building Telegram products: typed routing, async runtime,
stateful conversations, testing utilities, Mini App helpers, AI streaming, payments,
and production observability.

## Vision

Telegram bots are becoming real applications: they need reliable state, clean
developer experience, testable flows, Mini Apps, payments, AI responses, tracing,
and deployment patterns. Kudexgram aims to make that feel boringly good.

```python
from kudexgram import Bot, Context, Router

bot = Bot.from_env()
router = Router()


@router.command("start")
async def start(ctx: Context) -> str:
    return "Hey. Kudexgram is alive."


@router.text()
async def echo(message: str) -> str:
    return f"You said: {message}"


bot.include(router)
bot.run_polling()
```

## CLI

Kudexgram uses the short command name `kdx`.

```bash
kdx --help
kdx new mybot
cd mybot
python -m pip install -e ".[dev]"
copy .env.example .env
python bot.py
kdx dev
```

## Install for development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

If you use `uv`, the intended workflow is:

```bash
uv sync --extra dev
uv run pytest
uv run kdx --help
```

## MVP Goals

- Thin `Bot` facade over an application/runtime architecture.
- Async Telegram Bot API client with a typed core and codegen-ready boundaries.
- Router decorators for commands and text messages with compiled handler resolution.
- Context API with explicit `ctx: Context` injection and `ctx.reply(...)` sugar.
- Runtime boundary for polling, webhook, replay, and tests.
- Minimal production-shaped state engine for conversations.
- Testing DSL for feeding fake updates and asserting outgoing API calls.
- CLI entrypoint `kdx` for full project scaffolding and local development.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the current v0.1 architecture direction.

## Why not just aiogram or python-telegram-bot?

Those projects are excellent. Kudexgram is exploring a sharper product angle:

- **Testing-first** bot flows with replayable updates.
- **Production-first** runtime: rate limits, retries, tracing, queues, deploy recipes.
- **AI-native** helpers for streaming, tools, memory, and rich replies.
- **Mini-App-ready** backend helpers for Telegram Web Apps.
- **Codegen-ready** Telegram Bot API types so new Bot API releases can be adopted fast.

## Status

The repository is being bootstrapped. APIs may change freely until `0.1.0`.
