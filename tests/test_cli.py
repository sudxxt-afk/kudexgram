from typer.testing import CliRunner

from kudexgram.cli import app


def test_kdx_new_creates_project(tmp_path) -> None:
    runner = CliRunner()
    project = tmp_path / "mybot"

    result = runner.invoke(app, ["new", str(project)])

    assert result.exit_code == 0
    assert (project / "bot.py").exists()
    assert (project / "pyproject.toml").exists()
    assert (project / "README.md").exists()
    assert (project / ".env.example").exists()
    assert (project / ".gitignore").exists()
    assert (project / "tests" / "test_bot.py").exists()
    assert "kudexgram>=0.0.1" in (project / "pyproject.toml").read_text(encoding="utf-8")
    bot_template = (project / "bot.py").read_text(encoding="utf-8")
    test_template = (project / "tests" / "test_bot.py").read_text(encoding="utf-8")
    assert "from kudexgram import Bot, Context, InlineKeyboard" in bot_template
    assert "@bot.command(\"start\")" in bot_template
    assert "Router" not in bot_template
    assert '@bot.callback("profile")' in bot_template
    assert 'await scenario.tap("profile")' in test_template


def test_kdx_new_refuses_non_empty_directory_without_force(tmp_path) -> None:
    runner = CliRunner()
    project = tmp_path / "mybot"
    project.mkdir()
    (project / "keep.txt").write_text("do not touch", encoding="utf-8")

    result = runner.invoke(app, ["new", str(project)])

    assert result.exit_code != 0
    assert "already exists and is not empty" in result.output
    assert (project / "keep.txt").read_text(encoding="utf-8") == "do not touch"


def test_kdx_new_force_writes_generated_files(tmp_path) -> None:
    runner = CliRunner()
    project = tmp_path / "mybot"
    project.mkdir()
    (project / "keep.txt").write_text("keep me", encoding="utf-8")

    result = runner.invoke(app, ["new", str(project), "--force"])

    assert result.exit_code == 0
    assert (project / "bot.py").exists()
    assert (project / "keep.txt").read_text(encoding="utf-8") == "keep me"


def test_kdx_dev_runs_successfully(tmp_path) -> None:
    runner = CliRunner()
    bot_file = tmp_path / "bot.py"
    bot_file.write_text("print('hello bot')", encoding="utf-8")

    result = runner.invoke(app, ["dev", str(bot_file), "--once"])

    assert result.exit_code == 0
    assert "Starting local development runner for" in result.output
    assert "Running:" in result.output


def test_kdx_dev_errors_when_file_not_found(tmp_path) -> None:
    runner = CliRunner()
    bot_file = tmp_path / "does_not_exist.py"

    result = runner.invoke(app, ["dev", str(bot_file), "--once"])

    assert result.exit_code != 0
    assert "does not exist" in result.output
