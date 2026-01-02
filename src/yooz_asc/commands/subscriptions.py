"""Subscription management commands."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from yooz_asc.api.client import AppStoreConnectClient

app = typer.Typer(help="Manage subscriptions and pricing.")
console = Console()

# Sub-command groups
pricing_app = typer.Typer(help="Manage subscription pricing.")
offers_app = typer.Typer(help="Manage introductory and promotional offers.")

app.add_typer(pricing_app, name="pricing")
app.add_typer(offers_app, name="offers")


@app.command("list")
def list_subscriptions(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
) -> None:
    """List subscription groups and subscriptions for an app."""

    async def _list() -> None:
        client = AppStoreConnectClient()
        try:
            app_data = await client.get_app(bundle_id)
            if not app_data:
                console.print(f"[red]App not found:[/red] {bundle_id}")
                raise typer.Exit(1)

            app_id = app_data["id"]
            groups = await client.list_subscription_groups(app_id)

            if not groups:
                console.print("[dim]No subscription groups found[/dim]")
                return

            for group in groups:
                group_id = group["id"]
                group_name = group["attributes"]["referenceName"]
                console.print(f"\n[bold]Group:[/bold] {group_name}")

                subs = await client.list_subscriptions(group_id)
                if subs:
                    table = Table(show_header=True, header_style="bold")
                    table.add_column("Name")
                    table.add_column("Product ID")
                    table.add_column("State")
                    table.add_column("Family Sharing")

                    for sub in subs:
                        attrs = sub.get("attributes", {})
                        table.add_row(
                            attrs.get("name", ""),
                            attrs.get("productId", ""),
                            attrs.get("state", ""),
                            "Yes" if attrs.get("familySharable") else "No",
                        )

                    console.print(table)
                else:
                    console.print("  [dim]No subscriptions[/dim]")
        finally:
            await client.close()

    asyncio.run(_list())


@pricing_app.command("list")
def list_pricing(
    subscription_id: str = typer.Argument(..., help="Subscription ID"),
) -> None:
    """List current pricing for a subscription."""

    async def _list() -> None:
        client = AppStoreConnectClient()
        try:
            prices = await client.list_subscription_prices(subscription_id)

            if not prices:
                console.print("[dim]No pricing configured[/dim]")
                return

            table = Table(title="Subscription Prices")
            table.add_column("Territory")
            table.add_column("Price")
            table.add_column("Start Date")

            for price in prices:
                attrs = price.get("attributes", {})
                table.add_row(
                    attrs.get("territory", ""),
                    attrs.get("customerPrice", ""),
                    attrs.get("startDate", ""),
                )

            console.print(table)
        finally:
            await client.close()

    asyncio.run(_list())


@pricing_app.command("set")
def set_pricing(
    subscription_id: str = typer.Argument(..., help="Subscription ID"),
    price: float = typer.Option(..., "--price", "-p", help="Price in USD"),
    all_territories: bool = typer.Option(False, "--all", help="Apply to all territories"),
) -> None:
    """Set pricing for a subscription."""
    # TODO: Implement full pricing logic
    console.print("[yellow]Pricing configuration coming soon[/yellow]")
    console.print(f"Would set {subscription_id} to ${price}")


@offers_app.command("list")
def list_offers(
    subscription_id: str = typer.Argument(..., help="Subscription ID"),
) -> None:
    """List introductory offers for a subscription."""

    async def _list() -> None:
        client = AppStoreConnectClient()
        try:
            offers = await client.list_introductory_offers(subscription_id)

            if not offers:
                console.print("[dim]No introductory offers configured[/dim]")
                return

            table = Table(title="Introductory Offers")
            table.add_column("Territory")
            table.add_column("Type")
            table.add_column("Duration")
            table.add_column("Periods")

            for offer in offers:
                attrs = offer.get("attributes", {})
                table.add_row(
                    "All",  # TODO: Get territory from relationships
                    attrs.get("offerMode", ""),
                    attrs.get("duration", ""),
                    str(attrs.get("numberOfPeriods", "")),
                )

            console.print(table)
        finally:
            await client.close()

    asyncio.run(_list())


@offers_app.command("create")
def create_offer(
    subscription_id: str = typer.Argument(..., help="Subscription ID"),
    offer_type: str = typer.Option(
        ..., "--type", "-t", help="Offer type: free-trial, pay-as-you-go, pay-up-front"
    ),
    duration: str = typer.Option(..., "--duration", "-d", help="Duration: 3d, 1w, 2w, 1m, 3m, etc"),
    all_territories: bool = typer.Option(False, "--all", help="Apply to all territories"),
) -> None:
    """Create an introductory offer."""
    # TODO: Implement offer creation
    console.print("[yellow]Offer creation coming soon[/yellow]")
    console.print(f"Would create {offer_type} offer for {duration}")
