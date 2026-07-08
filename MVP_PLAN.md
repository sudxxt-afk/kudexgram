# Kudexgram MVP Plan

## Summary

Build a production-minded open-source Python SDK/framework for Telegram bots.
The MVP should prove the developer experience end to end: create a bot, register
typed handlers, run polling, keep simple state, test a conversation, and use the
short CLI command `kdx`.

## Public Interfaces

- `Bot`: thin facade over `Application`, with token configuration, router inclusion, plugin install, and `run_polling()`.
- `Application`: owns routers, plugins, dispatch, and lifecycle coordination.
- `Router`: decorators for `command`, `text`, and later callbacks, with compiled handler resolution.
- `Context` / `ctx`: explicit handler context plus convenience proxy, with `reply(...)` and access to update/message/chat/user.
- `Middleware`: `bot.use(...)` / `app.use(...)` pipeline around dispatch.
- `UpdateSource` / `PollingRunner`: runtime boundary for polling, webhook, queue, replay, and tests.
- `TelegramClient`: low-level async API client with `call(...)`, `send_message(...)`,
  `get_updates(...)`, retries, rate-limit handling, and readable errors.
- `MemoryStateStore`: development state adapter behind a production-shaped `StateStore` contract.
- `BotScenario`: testing DSL for feeding message updates and asserting replies/API calls.
- `kdx`: console command for project scaffolding and local dev.

## Implementation Milestones

1. Repository bootstrap: packaging, README, license, lint/test config.
2. Core models: minimal `Update`, `Message`, `Chat`, `User` using `msgspec`.
3. Client runtime: persistent `TelegramClient`, retry policy, polling source, runner,
   error handling, graceful shutdown.
4. Routing: command/text matching, compiled handler dispatch, context proxy, returned text rendering.
   - Unsupported handler parameters fail at registration with clear errors.
5. State: versioned in-memory state store and conversation-oriented example.
6. Testing: fake Telegram client, `bot.scenario()`, update feed helpers, outgoing message assertions.
   - Middleware order, short-circuiting, and handler signature validation are covered.
7. CLI: `kdx new <name>`, `kdx dev`, and `kdx --help`.
   - `kdx new` generates `pyproject.toml`, `README.md`, `.env.example`, `.gitignore`,
     `bot.py`, and `tests/test_bot.py`.
8. Docs/examples: echo bot, conversation bot, AI assistant stub.
9. Architecture docs: keep `ARCHITECTURE.md` updated with stable extension points before API freeze.

## Test Plan

- Router matching for command, text, and unmatched updates.
- Client payload tests with mocked HTTP transport.
- Client retry tests for Telegram `429`, HTTP `5xx`, non-retryable `4xx`, and network errors.
- Polling dispatch tests with fake updates.
- State lifecycle tests: set, get, clear.
- CLI smoke tests for `kdx --help` and project scaffolding in a temp directory.

## Defaults

- Python `3.11+`.
- MIT license.
- `msgspec` for fast core models.
- `httpx` for async HTTP.
- `typer` for CLI.
- Full Bot API coverage is intentionally out of MVP scope; the first release should be narrow, working, and easy to extend.
