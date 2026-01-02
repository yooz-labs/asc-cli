"""Main CLI entry point for yooz-asc."""

from typing import Optional

import typer
from rich.console import Console

from yooz_asc import __version__
from yooz_asc.commands import apps, auth, subscriptions, testflight

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


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]yooz-asc[/bold blue] version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """
    [bold blue]yooz-asc[/bold blue] - App Store Connect on your terminal.

    Manage subscriptions, pricing, TestFlight, and more.

    [dim]Get started:[/dim]
        asc auth login
        asc apps list
    """


if __name__ == "__main__":
    app()
