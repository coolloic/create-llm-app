from typer.testing import CliRunner
from create_llm_app.cli import app

runner = CliRunner()

def test_new_command_exists():
    result = runner.invoke(app, ["new", "myapp"])
    assert result.exit_code == 0
    assert "myapp" in result.output