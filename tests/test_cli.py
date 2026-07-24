import os
import py_compile
from pathlib import Path

from typer.testing import CliRunner

from create_llm_app.cli import app

runner = CliRunner()


def test_new_generates_project_with_flags(tmp_path):
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(
            app,
            ["new", "myapp", "--provider", "anthropic", "--type", "chat", "--no-tracing"],
        )
        assert result.exit_code == 0, result.output
        assert "myapp" in result.output

        proj = Path("myapp")
        assert (proj / "main.py").exists()
        assert (proj / "requirements.txt").exists()
        assert (proj / ".env.example").exists()

        # generated app is valid Python
        py_compile.compile(str(proj / "main.py"), doraise=True)
    finally:
        os.chdir(old_cwd)


def test_new_rejects_invalid_provider(tmp_path):
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(
            app,
            ["new", "myapp", "--provider", "cohere", "--type", "chat", "--no-tracing"],
        )
        assert result.exit_code != 0
    finally:
        os.chdir(old_cwd)
