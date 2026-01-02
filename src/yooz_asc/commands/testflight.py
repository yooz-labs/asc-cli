"""TestFlight management commands."""

import typer
from rich.console import Console

app = typer.Typer(help="Manage TestFlight builds and testers.")
console = Console()

# Sub-command groups
builds_app = typer.Typer(help="Manage builds.")
groups_app = typer.Typer(help="Manage beta groups.")
testers_app = typer.Typer(help="Manage testers.")

app.add_typer(builds_app, name="builds")
app.add_typer(groups_app, name="groups")
app.add_typer(testers_app, name="testers")


@builds_app.command("list")
def list_builds(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of builds to show"),
) -> None:
    """List TestFlight builds."""
    # TODO: Implement
    console.print("[yellow]Build listing coming soon[/yellow]")


@builds_app.command("expire")
def expire_build(
    build_id: str = typer.Argument(..., help="Build ID to expire"),
) -> None:
    """Expire a TestFlight build."""
    # TODO: Implement
    console.print("[yellow]Build expiration coming soon[/yellow]")


@groups_app.command("list")
def list_groups(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
) -> None:
    """List beta groups."""
    # TODO: Implement
    console.print("[yellow]Group listing coming soon[/yellow]")


@groups_app.command("create")
def create_group(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
    name: str = typer.Option(..., "--name", "-n", help="Group name"),
    public: bool = typer.Option(False, "--public", help="Create public link"),
) -> None:
    """Create a beta group."""
    # TODO: Implement
    console.print("[yellow]Group creation coming soon[/yellow]")


@testers_app.command("list")
def list_testers(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
) -> None:
    """List beta testers."""
    # TODO: Implement
    console.print("[yellow]Tester listing coming soon[/yellow]")


@testers_app.command("add")
def add_tester(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
    email: str = typer.Option(..., "--email", "-e", help="Tester email"),
    group: str | None = typer.Option(None, "--group", "-g", help="Beta group name"),
) -> None:
    """Add a beta tester."""
    # TODO: Implement
    console.print("[yellow]Tester addition coming soon[/yellow]")


@testers_app.command("remove")
def remove_tester(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
    email: str = typer.Option(..., "--email", "-e", help="Tester email"),
) -> None:
    """Remove a beta tester."""
    # TODO: Implement
    console.print("[yellow]Tester removal coming soon[/yellow]")
