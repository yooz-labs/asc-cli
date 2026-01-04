"""App management commands."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from asc_cli.api.client import AppStoreConnectClient

app = typer.Typer(help="Manage apps.")
console = Console()


@app.command("list")
def list_apps() -> None:
    """List all apps."""

    async def _list() -> None:
        client = AppStoreConnectClient()
        try:
            apps = await client.list_apps()

            if not apps:
                console.print("[dim]No apps found[/dim]")
                return

            table = Table(title="Apps")
            table.add_column("Name", style="bold")
            table.add_column("Bundle ID")
            table.add_column("SKU")
            table.add_column("ID", style="dim")

            for app_data in apps:
                attrs = app_data.get("attributes", {})
                table.add_row(
                    attrs.get("name", ""),
                    attrs.get("bundleId", ""),
                    attrs.get("sku", ""),
                    app_data.get("id", ""),
                )

            console.print(table)
        finally:
            await client.close()

    asyncio.run(_list())


@app.command("info")
def app_info(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
) -> None:
    """Get app details."""

    async def _info() -> None:
        client = AppStoreConnectClient()
        try:
            app_data = await client.get_app(bundle_id)

            if not app_data:
                console.print(f"[red]App not found:[/red] {bundle_id}")
                raise typer.Exit(1)

            attrs = app_data.get("attributes", {})

            console.print(f"\n[bold]{attrs.get('name', 'Unknown')}[/bold]")
            console.print(f"  Bundle ID: {attrs.get('bundleId', '')}")
            console.print(f"  SKU: {attrs.get('sku', '')}")
            console.print(f"  Primary Locale: {attrs.get('primaryLocale', '')}")
            console.print(f"  Content Rights: {attrs.get('contentRightsDeclaration', '')}")
            console.print(f"  ID: [dim]{app_data.get('id', '')}[/dim]")
        finally:
            await client.close()

    asyncio.run(_info())
