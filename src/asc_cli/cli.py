"""Main CLI entry point for asc-cli."""

import typer
from rich.console import Console

from asc_cli import __version__
from asc_cli.commands import apps, auth, bulk, subscriptions, testflight

app = typer.Typer(
    name="asc",
    help="A powerful CLI for Apple App Store Connect API.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()

# Register command groups
app.add_typer(auth.app, name="auth", help="Manage authentication")
app.add_typer(apps.app, name="apps", help="Manage apps")
app.add_typer(subscriptions.app, name="subscriptions", help="Manage subscriptions and pricing")
app.add_typer(testflight.app, name="testflight", help="Manage TestFlight builds and testers")
app.add_typer(bulk.app, name="bulk", help="Bulk operations from YAML configuration")


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]asc-cli[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """
    [bold blue]asc-cli[/bold blue] - App Store Connect on your terminal.

    Manage subscriptions, pricing, TestFlight, and more.

    [dim]Get started:[/dim]
        asc auth login
        asc apps list
    """


if __name__ == "__main__":
    app()
