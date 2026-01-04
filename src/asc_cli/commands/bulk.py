"""Bulk operations from YAML configuration files."""

import asyncio
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from asc_cli.api.client import AppStoreConnectClient
from asc_cli.config.schema import (
    IntroductoryOffer,
    OfferType,
    SubscriptionConfig,
    SubscriptionsConfig,
    generate_example_config,
)

app = typer.Typer(help="Bulk operations from YAML configuration.")
console = Console()


@app.command("apply")
def apply_config(
    config_file: Path = typer.Argument(..., help="Path to YAML configuration file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without applying"),
) -> None:
    """Apply subscription configuration from a YAML file.

    This command reads a YAML configuration file and applies:
    - Pricing for all specified subscriptions across territories
    - Introductory offers (free trials, promotions)

    Example:
        asc bulk apply subscriptions.yaml
        asc bulk apply subscriptions.yaml --dry-run
    """
    # Load configuration
    try:
        config = SubscriptionsConfig.from_yaml(config_file)
    except FileNotFoundError:
        console.print(f"[red]Configuration file not found:[/red] {config_file}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {e}")
        raise typer.Exit(1)

    # Override dry_run from CLI if specified
    if dry_run:
        config.dry_run = True

    console.print(f"[bold]Applying configuration for:[/bold] {config.app_bundle_id}")
    console.print(f"[dim]Subscriptions to configure: {len(config.subscriptions)}[/dim]")

    if config.dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    async def _apply() -> None:
        client = AppStoreConnectClient()
        try:
            # Get app and subscription info
            app_data = await client.get_app(config.app_bundle_id)
            if not app_data:
                console.print(f"[red]App not found:[/red] {config.app_bundle_id}")
                raise typer.Exit(1)

            app_id = app_data["id"]
            console.print(f"[green]Found app:[/green] {app_id}")

            # Get subscription groups and subscriptions
            groups = await client.list_subscription_groups(app_id)
            all_subscriptions: dict[str, dict[str, Any]] = {}

            for group in groups:
                subs = await client.list_subscriptions(group["id"])
                for sub in subs:
                    product_id = sub.get("attributes", {}).get("productId")
                    if product_id:
                        all_subscriptions[product_id] = sub

            # Process each subscription in config
            for sub_config in config.subscriptions:
                console.print(f"\n[bold]Processing:[/bold] {sub_config.product_id}")

                # Find subscription
                if sub_config.product_id not in all_subscriptions:
                    console.print("  [yellow]Subscription not found, skipping[/yellow]")
                    continue

                subscription = all_subscriptions[sub_config.product_id]
                subscription_id = subscription["id"]

                # Set subscription period if specified and not already set
                await _set_subscription_period(
                    client,
                    subscription_id,
                    subscription,
                    sub_config,
                    config.dry_run,
                )

                # Set availability first (required before pricing)
                await _set_availability(
                    client,
                    subscription_id,
                    sub_config.territories,
                    config.dry_run,
                )

                # Apply pricing
                await _apply_pricing(
                    client,
                    subscription_id,
                    sub_config.price_usd,
                    sub_config.territories,
                    config.dry_run,
                )

                # Apply offers
                for offer in sub_config.offers:
                    await _apply_offer(
                        client,
                        subscription_id,
                        offer,
                        config.dry_run,
                    )

            console.print("\n[green]Configuration applied successfully![/green]")

        finally:
            await client.close()

    asyncio.run(_apply())


async def _set_subscription_period(
    client: AppStoreConnectClient,
    subscription_id: str,
    subscription: dict[str, Any],
    sub_config: SubscriptionConfig,
    dry_run: bool,
) -> None:
    """Set subscription billing period if specified and not already set."""
    from asc_cli.api.client import APIError

    if sub_config.period is None:
        return  # No period specified in config

    current_period = subscription.get("attributes", {}).get("subscriptionPeriod")
    target_period = sub_config.period.to_api_value()

    if current_period == target_period:
        console.print(f"  [dim]Period already set to {target_period}[/dim]")
        return

    if current_period is not None:
        console.print(
            f"  [yellow]Period already set to {current_period}, "
            f"cannot change to {target_period}[/yellow]"
        )
        return

    console.print(f"  [dim]Setting period to {target_period}...[/dim]")

    if dry_run:
        console.print(f"  [yellow]Would set period to {target_period}[/yellow]")
        return

    try:
        await client.patch(
            f"subscriptions/{subscription_id}",
            {
                "data": {
                    "type": "subscriptions",
                    "id": subscription_id,
                    "attributes": {"subscriptionPeriod": target_period},
                }
            },
        )
        console.print(f"  [green]Set period to {target_period}[/green]")
    except APIError as e:
        console.print(f"  [red]Period error:[/red] {e}")


async def _set_availability(
    client: AppStoreConnectClient,
    subscription_id: str,
    territories: list[str] | str,
    dry_run: bool,
) -> None:
    """Set subscription availability for territories."""
    console.print("  [dim]Setting availability...[/dim]")

    # Get all territories if needed
    if territories == "all":
        all_terrs = await client.list_territories()
        territory_ids = [t["id"] for t in all_terrs]
    else:
        territory_ids = [t.upper() for t in territories]

    if dry_run:
        n_terr = len(territory_ids)
        console.print(f"  [yellow]Would set availability for {n_terr} territories[/yellow]")
        return

    try:
        await client.set_subscription_availability(
            subscription_id=subscription_id,
            territory_ids=territory_ids,
            available_in_new_territories=True,
        )
        console.print(f"  [green]Set availability for {len(territory_ids)} territories[/green]")
    except Exception as e:
        console.print(f"  [red]Availability error:[/red] {e}")


async def _apply_pricing(
    client: AppStoreConnectClient,
    subscription_id: str,
    price_usd: float,
    territories: list[str] | str,
    dry_run: bool,
) -> None:
    """Apply pricing to a subscription."""
    console.print(f"  [dim]Setting price: ${price_usd} USD[/dim]")

    # Find base price point
    base_price_point = await client.find_price_point_by_usd(
        subscription_id, price_usd, territory="USA"
    )

    if not base_price_point:
        console.print(f"  [red]No price point found for ${price_usd}[/red]")
        return

    # Get equalized price points
    equalized_points = await client.find_equalizing_price_points(
        subscription_id, base_price_point["id"]
    )

    # Filter territories if needed
    if territories != "all":
        territory_set = {t.upper() for t in territories}
        equalized_points = [
            pp
            for pp in equalized_points
            if pp.get("relationships", {}).get("territory", {}).get("data", {}).get("id")
            in territory_set
        ]

    console.print(f"  [dim]Found {len(equalized_points)} territory price points[/dim]")

    if dry_run:
        n_terr = len(equalized_points)
        console.print(f"  [yellow]Would set pricing for {n_terr} territories[/yellow]")
        return

    # Apply prices
    success = 0
    errors = 0
    for pp in equalized_points:
        try:
            await client.create_subscription_price(
                subscription_id=subscription_id,
                price_point_id=pp["id"],
            )
            success += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                console.print(f"  [red]Price error:[/red] {e}")

    console.print(f"  [green]Set pricing for {success} territories[/green]")


async def _apply_offer(
    client: AppStoreConnectClient,
    subscription_id: str,
    offer: IntroductoryOffer,
    dry_run: bool,
) -> None:
    """Apply an introductory offer to a subscription."""
    from asc_cli.commands.subscriptions import parse_duration

    # App Store Connect API expects uppercase snake_case
    offer_mode_map = {
        OfferType.FREE_TRIAL: "FREE_TRIAL",
        OfferType.PAY_AS_YOU_GO: "PAY_AS_YOU_GO",
        OfferType.PAY_UP_FRONT: "PAY_UP_FRONT",
    }

    offer_mode = offer_mode_map[offer.type]
    iso_duration, num_periods = parse_duration(offer.duration)

    console.print(f"  [dim]Creating {offer.type.value} offer: {offer.duration}[/dim]")

    # Get territories
    if offer.territories == "all":
        all_terrs = await client.list_territories()
        target_territories = [t["id"] for t in all_terrs]
    else:
        target_territories = [t.upper() for t in offer.territories]

    # Find price point for paid offers
    price_point_id: str | None = None
    if offer.price_usd is not None:
        price_point = await client.find_price_point_by_usd(
            subscription_id, offer.price_usd, territory="USA"
        )
        if price_point:
            price_point_id = price_point["id"]

    if dry_run:
        n_terr = len(target_territories)
        offer_name = offer.type.value
        console.print(f"  [yellow]Would create {offer_name} for {n_terr} territories[/yellow]")
        return

    # Create offers
    success = 0
    errors = 0
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
            success += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                console.print(f"  [red]Offer error ({territory_id}):[/red] {e}")

    console.print(f"  [green]Created offers for {success} territories[/green]")


@app.command("init")
def init_config(
    output: Path = typer.Option(
        Path("subscriptions.yaml"),
        "--output",
        "-o",
        help="Output file path",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
) -> None:
    """Generate an example configuration file.

    Creates a template YAML file with example subscriptions,
    pricing, and offers that you can customize.
    """
    if output.exists() and not force:
        console.print(f"[red]File already exists:[/red] {output}")
        console.print("[dim]Use --force to overwrite[/dim]")
        raise typer.Exit(1)

    generate_example_config(output)
    console.print(f"[green]Created example configuration:[/green] {output}")
    console.print("[dim]Edit this file and run: asc bulk apply subscriptions.yaml[/dim]")


@app.command("validate")
def validate_config(
    config_file: Path = typer.Argument(..., help="Path to YAML configuration file"),
) -> None:
    """Validate a configuration file without applying it.

    Checks the YAML syntax and schema, and verifies that
    subscriptions exist in App Store Connect.
    """
    try:
        config = SubscriptionsConfig.from_yaml(config_file)
    except FileNotFoundError:
        console.print(f"[red]File not found:[/red] {config_file}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Validation error:[/red] {e}")
        raise typer.Exit(1)

    console.print("[green]Configuration is valid![/green]\n")

    # Show summary
    table = Table(title="Configuration Summary")
    table.add_column("Property")
    table.add_column("Value")

    table.add_row("App Bundle ID", config.app_bundle_id)
    table.add_row("Subscriptions", str(len(config.subscriptions)))
    table.add_row("Dry Run", "Yes" if config.dry_run else "No")

    console.print(table)

    # Show subscriptions
    sub_table = Table(title="Subscriptions")
    sub_table.add_column("Product ID")
    sub_table.add_column("Price (USD)")
    sub_table.add_column("Territories")
    sub_table.add_column("Offers")

    for sub in config.subscriptions:
        territories = "all" if sub.territories == "all" else str(len(sub.territories))
        sub_table.add_row(
            sub.product_id,
            f"${sub.price_usd}",
            territories,
            str(len(sub.offers)),
        )

    console.print(sub_table)


@app.command("schema")
def export_schema(
    output: Path = typer.Option(
        Path("subscriptions.schema.json"),
        "--output",
        "-o",
        help="Output file path for JSON schema",
    ),
) -> None:
    """Export JSON schema for configuration validation.

    The schema can be used with YAML/JSON validators
    or IDEs for autocomplete support.
    """
    SubscriptionsConfig.write_json_schema(output)
    console.print(f"[green]Exported JSON schema:[/green] {output}")
    console.print("[dim]Use with your editor for validation and autocomplete[/dim]")
