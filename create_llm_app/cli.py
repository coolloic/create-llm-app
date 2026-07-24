from pathlib import Path

import typer

from .generator import generate_project
from .prompts import collect_config

app = typer.Typer(help="Scaffold runnable LLM applications.")


@app.callback()
def callback():
    """Scaffold runnable LLM applications."""


@app.command()
def new(
    name: str = typer.Argument(..., help="Project directory name"),
    provider: str = typer.Option(None, "--provider", "-p", help="anthropic | openai"),
    app_type: str = typer.Option(None, "--type", "-t", help="chat | rag | agent"),
    tracing: bool = typer.Option(None, "--tracing/--no-tracing", help="Enable LangSmith tracing"),
):
    """Create a new runnable LLM application in ./<name>."""
    try:
        config = collect_config(name, provider, app_type, tracing)
        written = generate_project(config, Path.cwd())
    except (ValueError, FileExistsError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    typer.secho(f"Created {config.name}/ with {len(written)} files.", fg=typer.colors.GREEN)
    typer.echo(f"Next steps:\n  cd {config.name}\n  pip install -r requirements.txt")
    typer.echo("  cp .env.example .env   # add your API key(s)\n  python main.py")


if __name__ == "__main__":
    app()
