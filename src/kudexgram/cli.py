from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Kudexgram developer toolkit.")


@app.command()
def new(name: str) -> None:
    """Create a minimal Kudexgram bot project."""
    root = Path(name)
    root.mkdir(parents=True, exist_ok=False)
    (root / "bot.py").write_text(
        """from kudexgram import Bot, Router, ctx

bot = Bot.from_env()
router = Router()


@router.command("start")
async def start() -> None:
    await ctx.reply("Hello from Kudexgram.")


bot.include(router)

if __name__ == "__main__":
    bot.run_polling()
""",
        encoding="utf-8",
    )
    (root / ".env.example").write_text("TELEGRAM_BOT_TOKEN=replace-me\n", encoding="utf-8")
    typer.echo(f"Created {root}")


@app.command()
def dev() -> None:
    """Start the local development runner."""
    typer.echo("kdx dev is planned for the MVP. Run your bot module directly for now.")


if __name__ == "__main__":
    app()

