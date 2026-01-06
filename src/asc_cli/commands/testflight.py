"""TestFlight management commands."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from asc_cli.api.client import APIError, AppStoreConnectClient

app = typer.Typer(help="Manage TestFlight builds and testers.")
console = Console()

# Sub-command groups
builds_app = typer.Typer(help="Manage builds.")
groups_app = typer.Typer(help="Manage beta groups.")
testers_app = typer.Typer(help="Manage testers.")

app.add_typer(builds_app, name="builds")
app.add_typer(groups_app, name="groups")
app.add_typer(testers_app, name="testers")


def run_async(coro):
    """Run an async function synchronously."""
    return asyncio.run(coro)


# ============================================================================
# Builds Commands
# ============================================================================


@builds_app.command("list")
def list_builds(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
    limit: int = typer.Option(10, "--limit", "-n", help="Number of builds to show"),
) -> None:
    """List TestFlight builds."""

    async def _list_builds():
        client = AppStoreConnectClient()
        try:
            # Get app first
            app_data = await client.get_app(bundle_id)
            if not app_data:
                console.print(f"[red]App not found: {bundle_id}[/red]")
                return

            app_id = app_data["id"]
            builds = await client.list_builds(app_id, limit=limit)

            if not builds:
                console.print("[yellow]No builds found[/yellow]")
                return

            table = Table(title=f"Builds for {bundle_id}")
            table.add_column("Version", style="cyan")
            table.add_column("Build", style="green")
            table.add_column("State", style="yellow")
            table.add_column("Uploaded", style="dim")
            table.add_column("ID", style="dim")

            for build in builds:
                attrs = build.get("attributes", {})
                table.add_row(
                    attrs.get("version", "N/A"),
                    str(attrs.get("minOsVersion", "N/A")),
                    attrs.get("processingState", "N/A"),
                    attrs.get("uploadedDate", "N/A")[:10] if attrs.get("uploadedDate") else "N/A",
                    build["id"],
                )

            console.print(table)
        finally:
            await client.close()

    run_async(_list_builds())


@builds_app.command("update")
def update_build(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
    build: str = typer.Option(..., "--build", "-b", help="Build number"),
    whats_new: str = typer.Option(None, "--whats-new", "-w", help="What's New text"),
    whats_new_file: Path = typer.Option(
        None, "--whats-new-file", "-f", help="File containing What's New text"
    ),
    locale: str = typer.Option("en-US", "--locale", "-l", help="Locale for What's New"),
) -> None:
    """Update build info (What's New text)."""
    if not whats_new and not whats_new_file:
        console.print("[red]Either --whats-new or --whats-new-file is required[/red]")
        raise typer.Exit(1)

    if whats_new_file:
        if not whats_new_file.exists():
            console.print(f"[red]File not found: {whats_new_file}[/red]")
            raise typer.Exit(1)
        whats_new = whats_new_file.read_text().strip()

    async def _update_build():
        client = AppStoreConnectClient()
        try:
            # Get app
            app_data = await client.get_app(bundle_id)
            if not app_data:
                console.print(f"[red]App not found: {bundle_id}[/red]")
                return

            app_id = app_data["id"]

            # Find build by version
            build_data = await client.get_build_by_version(app_id, build)
            if not build_data:
                console.print(f"[red]Build {build} not found[/red]")
                return

            build_id = build_data["id"]

            # Check for existing localization
            localizations = await client.list_beta_build_localizations(build_id)
            existing = next(
                (loc for loc in localizations if loc["attributes"]["locale"] == locale), None
            )

            if existing:
                # Update existing
                await client.update_beta_build_localization(existing["id"], whats_new)
                console.print(f"[green]Updated What's New for build {build} ({locale})[/green]")
            else:
                # Create new
                await client.create_beta_build_localization(build_id, locale, whats_new)
                console.print(f"[green]Created What's New for build {build} ({locale})[/green]")
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_update_build())


@builds_app.command("encryption")
def set_encryption(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
    build: str = typer.Option(..., "--build", "-b", help="Build number"),
    uses_encryption: bool = typer.Option(
        False, "--uses-encryption/--no-encryption", help="App uses encryption"
    ),
    exempt: bool = typer.Option(
        True, "--exempt/--not-exempt", help="Encryption is exempt (standard HTTPS)"
    ),
) -> None:
    """Set encryption declaration for a build."""

    async def _set_encryption():
        client = AppStoreConnectClient()
        try:
            # Get app
            app_data = await client.get_app(bundle_id)
            if not app_data:
                console.print(f"[red]App not found: {bundle_id}[/red]")
                return

            app_id = app_data["id"]

            # Find build
            build_data = await client.get_build_by_version(app_id, build)
            if not build_data:
                console.print(f"[red]Build {build} not found[/red]")
                return

            build_id = build_data["id"]

            # Create encryption declaration
            await client.create_app_encryption_declaration(build_id, uses_encryption, exempt)

            if not uses_encryption:
                console.print(
                    f"[green]Set encryption declaration: No encryption (build {build})[/green]"
                )
            elif exempt:
                console.print(f"[green]Set encryption declaration: Exempt (build {build})[/green]")
            else:
                console.print(
                    f"[green]Set encryption declaration: Uses encryption (build {build})[/green]"
                )
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_set_encryption())


@builds_app.command("submit")
def submit_build(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
    build: str = typer.Option(..., "--build", "-b", help="Build number"),
) -> None:
    """Submit a build for TestFlight beta review."""

    async def _submit_build():
        client = AppStoreConnectClient()
        try:
            # Get app
            app_data = await client.get_app(bundle_id)
            if not app_data:
                console.print(f"[red]App not found: {bundle_id}[/red]")
                return

            app_id = app_data["id"]

            # Find build
            build_data = await client.get_build_by_version(app_id, build)
            if not build_data:
                console.print(f"[red]Build {build} not found[/red]")
                return

            build_id = build_data["id"]

            # Submit for review
            await client.submit_for_beta_review(build_id)
            console.print(f"[green]Submitted build {build} for TestFlight review[/green]")
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_submit_build())


@builds_app.command("expire")
def expire_build(
    build_id: str = typer.Argument(..., help="Build ID to expire"),
) -> None:
    """Expire a TestFlight build."""
    # Note: Build expiration uses PATCH to set expired: true
    console.print("[yellow]Build expiration coming soon[/yellow]")


# ============================================================================
# Groups Commands
# ============================================================================


@groups_app.command("list")
def list_groups(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
) -> None:
    """List beta groups."""

    async def _list_groups():
        client = AppStoreConnectClient()
        try:
            app_data = await client.get_app(bundle_id)
            if not app_data:
                console.print(f"[red]App not found: {bundle_id}[/red]")
                return

            app_id = app_data["id"]
            groups = await client.list_beta_groups(app_id)

            if not groups:
                console.print("[yellow]No beta groups found[/yellow]")
                return

            table = Table(title=f"Beta Groups for {bundle_id}")
            table.add_column("Name", style="cyan")
            table.add_column("Internal", style="green")
            table.add_column("Public Link", style="yellow")
            table.add_column("Feedback", style="dim")
            table.add_column("ID", style="dim")

            for group in groups:
                attrs = group.get("attributes", {})
                table.add_row(
                    attrs.get("name", "N/A"),
                    "Yes" if attrs.get("isInternalGroup") else "No",
                    "Enabled" if attrs.get("publicLinkEnabled") else "Disabled",
                    "Yes" if attrs.get("feedbackEnabled") else "No",
                    group["id"],
                )

            console.print(table)
        finally:
            await client.close()

    run_async(_list_groups())


@groups_app.command("create")
def create_group(
    bundle_id: str = typer.Argument(..., help="App bundle ID"),
    name: str = typer.Option(..., "--name", "-n", help="Group name"),
    public: bool = typer.Option(False, "--public", help="Enable public TestFlight link"),
    internal: bool = typer.Option(False, "--internal", help="Create as internal group"),
    public_limit: int = typer.Option(None, "--public-limit", help="Max testers via public link"),
) -> None:
    """Create a beta group."""

    async def _create_group():
        client = AppStoreConnectClient()
        try:
            app_data = await client.get_app(bundle_id)
            if not app_data:
                console.print(f"[red]App not found: {bundle_id}[/red]")
                return

            app_id = app_data["id"]
            result = await client.create_beta_group(
                app_id,
                name,
                is_internal=internal,
                public_link_enabled=public,
                public_link_limit=public_limit,
            )

            group_id = result.get("data", {}).get("id", "unknown")
            console.print(f"[green]Created beta group '{name}' (ID: {group_id})[/green]")

            if public:
                public_link = result.get("data", {}).get("attributes", {}).get("publicLink")
                if public_link:
                    console.print(f"[cyan]Public link: {public_link}[/cyan]")
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_create_group())


@groups_app.command("delete")
def delete_group(
    group_id: str = typer.Argument(..., help="Beta group ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Delete a beta group."""

    if not force:
        confirm = typer.confirm(f"Delete beta group {group_id}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    async def _delete_group():
        client = AppStoreConnectClient()
        try:
            success = await client.delete_beta_group(group_id)
            if success:
                console.print(f"[green]Deleted beta group {group_id}[/green]")
            else:
                console.print(f"[red]Failed to delete beta group {group_id}[/red]")
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_delete_group())


@groups_app.command("add-build")
def add_build_to_group(
    group_id: str = typer.Argument(..., help="Beta group ID"),
    build_id: str = typer.Option(..., "--build", "-b", help="Build ID to add"),
) -> None:
    """Add a build to a beta group."""

    async def _add_build():
        client = AppStoreConnectClient()
        try:
            await client.add_builds_to_beta_group(group_id, [build_id])
            console.print(f"[green]Added build {build_id} to group {group_id}[/green]")
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_add_build())


# ============================================================================
# Testers Commands
# ============================================================================


@testers_app.command("list")
def list_testers(
    bundle_id: str = typer.Argument(None, help="App bundle ID (optional)"),
    email: str = typer.Option(None, "--email", "-e", help="Filter by email"),
    limit: int = typer.Option(50, "--limit", "-n", help="Number of testers to show"),
) -> None:
    """List beta testers."""

    async def _list_testers():
        client = AppStoreConnectClient()
        try:
            app_id = None
            if bundle_id:
                app_data = await client.get_app(bundle_id)
                if not app_data:
                    console.print(f"[red]App not found: {bundle_id}[/red]")
                    return
                app_id = app_data["id"]

            testers = await client.list_beta_testers(app_id=app_id, email=email, limit=limit)

            if not testers:
                console.print("[yellow]No testers found[/yellow]")
                return

            table = Table(title="Beta Testers")
            table.add_column("Email", style="cyan")
            table.add_column("First Name", style="green")
            table.add_column("Last Name", style="green")
            table.add_column("Invite Type", style="yellow")
            table.add_column("ID", style="dim")

            for tester in testers:
                attrs = tester.get("attributes", {})
                table.add_row(
                    attrs.get("email", "N/A"),
                    attrs.get("firstName", "N/A"),
                    attrs.get("lastName", "N/A"),
                    attrs.get("inviteType", "N/A"),
                    tester["id"],
                )

            console.print(table)
        finally:
            await client.close()

    run_async(_list_testers())


@testers_app.command("add")
def add_tester(
    email: str = typer.Option(..., "--email", "-e", help="Tester email"),
    first_name: str = typer.Option(None, "--first-name", help="Tester first name"),
    last_name: str = typer.Option(None, "--last-name", help="Tester last name"),
    group: str = typer.Option(None, "--group", "-g", help="Beta group ID to add tester to"),
) -> None:
    """Add a beta tester."""

    async def _add_tester():
        client = AppStoreConnectClient()
        try:
            group_ids = [group] if group else None
            result = await client.create_beta_tester(
                email=email,
                first_name=first_name,
                last_name=last_name,
                group_ids=group_ids,
            )
            tester_id = result.get("data", {}).get("id", "unknown")
            console.print(f"[green]Added tester {email} (ID: {tester_id})[/green]")
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_add_tester())


@testers_app.command("remove")
def remove_tester(
    tester_id: str = typer.Argument(..., help="Tester ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Remove a beta tester."""

    if not force:
        confirm = typer.confirm(f"Remove tester {tester_id}?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    async def _remove_tester():
        client = AppStoreConnectClient()
        try:
            success = await client.delete_beta_tester(tester_id)
            if success:
                console.print(f"[green]Removed tester {tester_id}[/green]")
            else:
                console.print(f"[red]Failed to remove tester {tester_id}[/red]")
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_remove_tester())


@testers_app.command("add-to-group")
def add_tester_to_group(
    tester_id: str = typer.Argument(..., help="Tester ID"),
    group_id: str = typer.Option(..., "--group", "-g", help="Beta group ID"),
) -> None:
    """Add a tester to a beta group."""

    async def _add_to_group():
        client = AppStoreConnectClient()
        try:
            await client.add_beta_tester_to_groups(tester_id, [group_id])
            console.print(f"[green]Added tester {tester_id} to group {group_id}[/green]")
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_add_to_group())


@testers_app.command("remove-from-group")
def remove_tester_from_group(
    tester_id: str = typer.Argument(..., help="Tester ID"),
    group_id: str = typer.Option(..., "--group", "-g", help="Beta group ID"),
) -> None:
    """Remove a tester from a beta group."""

    async def _remove_from_group():
        client = AppStoreConnectClient()
        try:
            await client.remove_beta_tester_from_groups(tester_id, [group_id])
            console.print(f"[green]Removed tester {tester_id} from group {group_id}[/green]")
        except APIError as e:
            console.print(f"[red]API Error: {e.message}[/red]")
        finally:
            await client.close()

    run_async(_remove_from_group())
