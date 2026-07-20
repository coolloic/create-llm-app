import typer

app = typer.Typer(help="Scaffold runnable LLM applications.")


@app.callback()
def main():
    """Scaffold runnable LLM applications."""


@app.command()
def new(name: str = typer.Argument(..., help="Project directory name")):
    """Create a new LLM application in ./<name>."""
    typer.echo(f"(placeholder) would create project: {name}")


if __name__ == "__main__":
    app()
