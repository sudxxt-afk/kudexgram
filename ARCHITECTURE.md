# Kudexgram Architecture

Kudexgram is designed as a production framework, not only a Telegram Bot API
wrapper. The public API should stay small and friendly, while the internals are
split into stable extension points.

## Layer Model

- `kudexgram.bot`: user-facing facade. Keeps the nice `Bot.from_env()`,
  `bot.include(router)`, and `bot.run_polling()` workflow.
- `kudexgram.app`: application container. Owns routers, plugins, dispatch, and
  lifecycle coordination.
- `kudexgram.runtime`: update sources and runners. Polling, webhook, replay, and
  test sources should all feed updates through the same dispatch path.
- `kudexgram.router`: route registration, filters, compiled handler argument
  resolution, and result rendering.
- `kudexgram.context`: per-update request scope and helper sugar such as `ctx`.
- `kudexgram.client`: long-lived Telegram API client and transport policies.
- `kudexgram.state`: storage contracts and in-memory development adapter.
- `kudexgram.testing`: fake client and future scenario/replay DSL.

## Public API Direction

The preferred handler style is explicit context injection:

```python
from kudexgram import Bot, Context, Router

bot = Bot.from_env()
router = Router()


@router.command("start")
async def start(ctx: Context) -> str:
    return "Hey. Kudexgram is alive."


bot.include(router)
bot.run_polling()
```

Returning `str` is rendered as `ctx.reply(...)`. The global `ctx` proxy remains
as a convenience for tiny bots, but explicit `ctx: Context` is the stable path
for production code, dependency injection, sessions, and testing.

## Runtime Contract

Every runtime is an `UpdateSource` plus a runner:

- polling fetches updates from Telegram and commits offsets after successful
  dispatch;
- webhook adapters will decode incoming updates and fast-ack HTTP requests;
- testing/replay sources can feed stored updates into the same application.

This prevents polling, webhook, and tests from becoming separate frameworks.

## Extension Points

First-class interfaces should stay explicit:

- `Plugin.setup(app)` for installing routes, middleware, state stores, and
  integrations;
- `UpdateSource` for polling, webhook, queue, replay, and tests;
- `StateStore` for memory, Redis, Postgres, and custom persistence;
- handler resolvers and result renderers for dependency injection and response
  rendering.

Kudexgram should avoid automatic plugin discovery before `0.1`; explicit
`bot.install(plugin)` is easier to reason about and test.

## State And Conversations

The MVP keeps a memory store, but the contract should already point at
production needs: namespace, TTL, versioned records, and optional locks. A
conversation engine should be built on top of session storage rather than mixed
into the router.

## Bot API Strategy

Generated Bot API models and methods belong under a future
`kudexgram.api.generated` package. Hand-written code should focus on transport,
errors, policies, and ergonomic helpers. This keeps new Telegram Bot API releases
from forcing runtime rewrites.

## Non-Negotiables

- One long-lived HTTP client per bot by default.
- Handler signatures compiled at route registration, not inspected on every
  update.
- Offset commits happen after dispatch, not before.
- Tests must be able to run without Telegram.
- `kdx` remains the CLI entrypoint.

