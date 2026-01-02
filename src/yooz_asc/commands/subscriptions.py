"""Subscription management commands."""

import asyncio

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
    price: float = typer.Option(..., "--price", "-p", help="Base price in USD"),
    equalize: bool = typer.Option(
        True,
        "--equalize/--no-equalize",
        help="Use Apple's price equalization for other territories",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying"),
    territories: list[str] | None = typer.Option(
        None, "--territory", "-t", help="Specific territories (default: all)"
    ),
) -> None:
    """Set pricing for a subscription across territories.

    Uses Apple's automatic price equalization to set appropriate prices
    in all territories based on a USD base price.

    Examples:
        asc subscriptions pricing set SUB_ID --price 2.99
        asc subscriptions pricing set SUB_ID --price 2.99 --dry-run
        asc subscriptions pricing set SUB_ID --price 2.99 -t USA -t GBR
    """

    async def _set_pricing() -> None:
        from rich.progress import Progress, SpinnerColumn, TextColumn

        client = AppStoreConnectClient()
        try:
            # Step 1: Find the base price point in USA
            console.print(f"[dim]Finding ${price} price point in USA...[/dim]")
            base_price_point = await client.find_price_point_by_usd(
                subscription_id, price, territory="USA"
            )

            if not base_price_point:
                console.print(f"[red]No price point found for ${price} USD[/red]")
                console.print(
                    "[dim]Hint: Apple has specific price tiers. Try 0.99, 1.99, 2.99, etc.[/dim]"
                )
                raise typer.Exit(1)

            base_pp_id = base_price_point["id"]
            console.print(f"[green]Found price point:[/green] {base_pp_id}")

            # Step 2: Get equalizing price points for all territories
            console.print("[dim]Fetching equalized prices for all territories...[/dim]")
            equalized_points = await client.find_equalizing_price_points(
                subscription_id, base_pp_id
            )

            # Filter territories if specified
            if territories:
                territory_set = {t.upper() for t in territories}
                equalized_points = [
                    pp
                    for pp in equalized_points
                    if pp.get("relationships", {}).get("territory", {}).get("data", {}).get("id")
                    in territory_set
                ]

            console.print(f"[green]Found {len(equalized_points)} territory price points[/green]")

            if dry_run:
                # Show what would be set
                table = Table(title="Pricing Preview (Dry Run)")
                table.add_column("Territory")
                table.add_column("Price")
                table.add_column("Currency")

                for pp in equalized_points[:20]:  # Show first 20
                    attrs = pp.get("attributes", {})
                    territory = (
                        pp.get("relationships", {})
                        .get("territory", {})
                        .get("data", {})
                        .get("id", "")
                    )
                    table.add_row(
                        territory,
                        attrs.get("customerPrice", ""),
                        attrs.get("proceeds", ""),  # This shows currency info
                    )

                console.print(table)
                if len(equalized_points) > 20:
                    console.print(
                        f"[dim]... and {len(equalized_points) - 20} more territories[/dim]"
                    )
                console.print("\n[yellow]Dry run - no changes made[/yellow]")
                return

            # Step 3: Create subscription prices for each territory
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Setting prices for {len(equalized_points)} territories...",
                    total=len(equalized_points),
                )

                success_count = 0
                error_count = 0

                for pp in equalized_points:
                    pp_id = pp["id"]
                    territory = (
                        pp.get("relationships", {})
                        .get("territory", {})
                        .get("data", {})
                        .get("id", "")
                    )

                    try:
                        await client.create_subscription_price(
                            subscription_id=subscription_id,
                            price_point_id=pp_id,
                        )
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        if error_count <= 3:  # Show first few errors
                            console.print(f"[red]Error setting {territory}:[/red] {e}")

                    progress.advance(task)

            console.print(
                f"\n[green]Successfully set prices for {success_count} territories[/green]"
            )
            if error_count > 0:
                console.print(f"[yellow]Failed for {error_count} territories[/yellow]")

        finally:
            await client.close()

    asyncio.run(_set_pricing())


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


def parse_duration(duration: str) -> tuple[str, int]:
    """Parse duration string to ISO 8601 duration and number of periods.

    Args:
        duration: Human-friendly duration (e.g., "3d", "1w", "2w", "1m", "3m", "6m", "1y")

    Returns:
        Tuple of (ISO 8601 duration, number_of_periods)

    Examples:
        "3d" -> ("P3D", 1)
        "1w" -> ("P1W", 1)
        "2w" -> ("P2W", 1)
        "1m" -> ("P1M", 1)
        "3m" -> ("P1M", 3)  # 3 periods of 1 month
        "6m" -> ("P1M", 6)
        "1y" -> ("P1Y", 1)
    """
    import re

    match = re.match(r"^(\d+)([dwmy])$", duration.lower())
    if not match:
        raise ValueError(f"Invalid duration format: {duration}. Use 3d, 1w, 2w, 1m, 3m, 6m, 1y")

    value = int(match.group(1))
    unit = match.group(2)

    unit_map = {"d": "D", "w": "W", "m": "M", "y": "Y"}
    iso_unit = unit_map[unit]

    # For months > 1, we use multiple periods of 1 month (for pay-as-you-go)
    if unit == "m" and value > 1:
        return "P1M", value
    elif unit == "y" and value > 1:
        return "P1Y", value

    return f"P{value}{iso_unit}", 1


@offers_app.command("create")
def create_offer(
    subscription_id: str = typer.Argument(..., help="Subscription ID"),
    offer_type: str = typer.Option(
        ..., "--type", "-t", help="Offer type: free-trial, pay-as-you-go, pay-up-front"
    ),
    duration: str = typer.Option(
        ..., "--duration", "-d", help="Duration: 3d, 1w, 2w, 1m, 3m, 6m, 1y"
    ),
    price: float | None = typer.Option(
        None, "--price", "-p", help="Offer price in USD (for pay-as-you-go/pay-up-front)"
    ),
    all_territories: bool = typer.Option(False, "--all", "-a", help="Apply to all territories"),
    territories: list[str] | None = typer.Option(None, "--territory", help="Specific territories"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without applying"),
) -> None:
    """Create an introductory offer for a subscription.

    Examples:
        # 2-week free trial for all territories
        asc subscriptions offers create SUB_ID -t free-trial -d 2w --all

        # $1.99/month for 3 months (pay-as-you-go)
        asc subscriptions offers create SUB_ID -t pay-as-you-go -d 3m -p 1.99 --all

        # $9.99 for 3 months upfront (pay-up-front)
        asc subscriptions offers create SUB_ID -t pay-up-front -d 3m -p 9.99 --all
    """
    # Validate offer type
    offer_mode_map = {
        "free-trial": "freeTrial",
        "pay-as-you-go": "payAsYouGo",
        "pay-up-front": "payUpFront",
    }

    if offer_type not in offer_mode_map:
        console.print(f"[red]Invalid offer type:[/red] {offer_type}")
        console.print("[dim]Valid types: free-trial, pay-as-you-go, pay-up-front[/dim]")
        raise typer.Exit(1)

    offer_mode = offer_mode_map[offer_type]

    # Validate price requirement
    if offer_type != "free-trial" and price is None:
        console.print(f"[red]Price required for {offer_type} offers[/red]")
        raise typer.Exit(1)

    # Parse duration
    try:
        iso_duration, num_periods = parse_duration(duration)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    async def _create_offer() -> None:
        from rich.progress import Progress, SpinnerColumn, TextColumn

        client = AppStoreConnectClient()
        try:
            # Get list of territories to apply to
            if all_territories:
                console.print("[dim]Fetching all territories...[/dim]")
                all_terrs = await client.list_territories()
                target_territories = [t["id"] for t in all_terrs]
            elif territories:
                target_territories = [t.upper() for t in territories]
            else:
                console.print("[red]Specify --all or --territory[/red]")
                raise typer.Exit(1)

            console.print(f"[green]Will apply to {len(target_territories)} territories[/green]")

            # For paid offers, find the price point
            price_point_id: str | None = None
            if price is not None:
                console.print(f"[dim]Finding ${price} price point...[/dim]")
                price_point = await client.find_price_point_by_usd(
                    subscription_id, price, territory="USA"
                )
                if not price_point:
                    console.print(f"[red]No price point found for ${price} USD[/red]")
                    raise typer.Exit(1)
                price_point_id = price_point["id"]
                console.print(f"[green]Found price point:[/green] {price_point_id}")

            if dry_run:
                console.print("\n[bold]Dry Run Preview:[/bold]")
                console.print(f"  Offer Type: {offer_type}")
                console.print(f"  Duration: {iso_duration} x {num_periods} periods")
                if price:
                    console.print(f"  Price: ${price}")
                console.print(f"  Territories: {len(target_territories)}")
                console.print("\n[yellow]Dry run - no changes made[/yellow]")
                return

            # Create offers for each territory
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Creating offers for {len(target_territories)} territories...",
                    total=len(target_territories),
                )

                success_count = 0
                error_count = 0

                for territory_id in target_territories:
                    try:
                        await client.create_introductory_offer(
                            subscription_id=subscription_id,
                            territory_id=territory_id,
                            offer_mode=offer_mode,
                            duration=iso_duration,
                            number_of_periods=num_periods,
                            subscription_price_point_id=price_point_id,
                        )
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        if error_count <= 3:
                            console.print(f"[red]Error for {territory_id}:[/red] {e}")

                    progress.advance(task)

            console.print(f"\n[green]Created offers for {success_count} territories[/green]")
            if error_count > 0:
                console.print(f"[yellow]Failed for {error_count} territories[/yellow]")

        finally:
            await client.close()

    asyncio.run(_create_offer())


@offers_app.command("delete")
def delete_offer(
    offer_id: str = typer.Argument(..., help="Introductory offer ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete an introductory offer."""

    if not force:
        confirm = typer.confirm(f"Delete offer {offer_id}?")
        if not confirm:
            raise typer.Abort()

    async def _delete() -> None:
        client = AppStoreConnectClient()
        try:
            success = await client.delete_introductory_offer(offer_id)
            if success:
                console.print(f"[green]Deleted offer {offer_id}[/green]")
            else:
                console.print(f"[red]Failed to delete offer {offer_id}[/red]")
        finally:
            await client.close()

    asyncio.run(_delete())
