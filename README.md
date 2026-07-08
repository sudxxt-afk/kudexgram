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

## Manifesto

Kudexgram makes Telegram bots feel small when they are small, and stay
maintainable when they grow.

Write handlers as product logic. Return replies directly. Test conversations like
conversations. Scale into explicit context, state, middleware, plugins, and
production runtimes only when you need them.

```python
from kudexgram import Bot, Context

bot = Bot.from_env()


@bot.command("start")
async def start(ctx: Context) -> str:
    return "Hey. Kudexgram is alive."


@bot.text()
async def echo(message: str) -> str:
    return f"You said: {message}"


bot.run_polling()
```

Middleware stays explicit when a bot grows:

```python
@bot.use
async def log_chat(ctx: Context, next) -> bool:
    print(ctx.chat_id)
    return await next()
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
- Telegram API retries for rate limits, temporary HTTP failures, and network timeouts.
- `Bot` decorators for small bots, plus `Router` for modular projects.
- Router decorators for commands and text messages with compiled handler resolution.
- Context API with explicit `ctx: Context` injection and `ctx.reply(...)` sugar.
- Middleware pipeline with `bot.use(...)`.
- Clear handler signature errors for unsupported parameters.
- Runtime boundary for polling, webhook, replay, and tests.
- Minimal production-shaped state engine for conversations.
- Testing DSL for conversation-style tests with `bot.scenario()`.
- CLI entrypoint `kdx` for full project scaffolding and local development.

## Testing DSL

Kudexgram tests can read like a Telegram chat:

```python
scenario = bot.scenario(chat_id=42, user_id=7, first_name="Ada")

await scenario.send_message("/start")

scenario.assert_handled()
scenario.assert_last_reply("Hey Ada. Kudexgram is alive.")
scenario.assert_api_called("sendMessage")
```

## Client Reliability

`TelegramClient` has a small production-minded retry policy:

- Telegram `429` errors use `parameters.retry_after`.
- Temporary HTTP `5xx` responses retry with exponential backoff.
- Network timeouts and network errors retry before raising `TelegramNetworkError`.
- Non-retryable Telegram errors raise clear `TelegramAPIError` subclasses.

```python
client = TelegramClient("token", retry_attempts=3, retry_backoff=0.5)
```

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
