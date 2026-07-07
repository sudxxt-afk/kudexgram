from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Kudexgram developer toolkit.")


@app.command()
def new(
    name: str,
    *,
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite an existing project folder.",
    ),
) -> None:
    """Create a Kudexgram bot project."""
    root = Path(name)
    if root.exists() and any(root.iterdir()) and not force:
        raise typer.BadParameter(
            f"{root} already exists and is not empty. Use --force to overwrite generated files."
        )

    root.mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(exist_ok=True)

    files = {
        ".env.example": _env_template(),
        ".gitignore": _gitignore_template(),
        "README.md": _readme_template(root.name),
        "bot.py": _bot_template(),
        "pyproject.toml": _pyproject_template(root.name),
        "tests/test_bot.py": _test_template(),
    }

    for relative_path, content in files.items():
        path = root / relative_path
        path.write_text(content, encoding="utf-8")

    typer.echo(f"Created {root}")
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo(f"  cd {root}")
    typer.echo('  python -m pip install -e ".[dev]"')
    typer.echo("  copy .env.example .env")
    typer.echo("  python bot.py")


def _bot_template() -> str:
    return """from kudexgram import Bot, Context, Router


bot = Bot.from_env()
router = Router()


@router.command("start")
async def start(ctx: Context) -> str:
    user = ctx.message.from_.first_name if ctx.message and ctx.message.from_ else "there"
    return f"Hey {user}. Kudexgram is alive."


@router.text()
async def echo(message: str) -> str:
    return f"You said: {message}"


bot.include(router)

if __name__ == "__main__":
    bot.run_polling()
"""


def _env_template() -> str:
    return "TELEGRAM_BOT_TOKEN=replace-me\n"


def _gitignore_template() -> str:
    return """.env
.venv/
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/
.ruff_cache/
"""


def _pyproject_template(project_name: str) -> str:
    package_name = _normalize_package_name(project_name)
    return f"""[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "0.1.0"
description = "A Telegram bot built with Kudexgram."
requires-python = ">=3.11"
dependencies = [
  "kudexgram>=0.0.1",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "pytest-asyncio>=0.23",
  "ruff>=0.6",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "ASYNC"]

[tool.hatch.build.targets.wheel]
py-modules = ["bot"]

# Import package-safe name reserved for future generated modules: {package_name}
"""


def _readme_template(project_name: str) -> str:
    return f"""# {project_name}

Telegram bot built with Kudexgram.

## Setup

```powershell
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install -e ".[dev]"
copy .env.example .env
```

Put your BotFather token into `.env` or export it:

```powershell
$env:TELEGRAM_BOT_TOKEN="your-token"
python bot.py
```

## Test

```powershell
pytest
ruff check .
```
"""


def _test_template() -> str:
    return """import os

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from bot import bot


async def test_start_command_replies() -> None:
    scenario = bot.scenario(chat_id=42, user_id=7, first_name="Ada", username="ada")

    await scenario.send_message("/start")

    scenario.assert_handled()
    scenario.assert_last_reply("Hey Ada. Kudexgram is alive.")


async def test_echo_replies_with_message_text() -> None:
    scenario = bot.scenario(chat_id=42)

    await scenario.send_message("ping")

    scenario.assert_last_reply("You said: ping")
"""


def _normalize_package_name(name: str) -> str:
    normalized = "".join(character if character.isalnum() else "_" for character in name.lower())
    return normalized.strip("_") or "bot"


@app.command()
def dev() -> None:
    """Start the local development runner."""
    typer.echo("kdx dev is planned for the MVP. Run your bot module directly for now.")


if __name__ == "__main__":
    app()
