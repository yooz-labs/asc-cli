"""Authentication commands."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from asc_cli.api.auth import CONFIG_DIR, AuthManager, Credentials

app = typer.Typer(help="Manage authentication credentials.")
console = Console()


@app.command()
def login(
    issuer_id: str | None = typer.Option(None, "--issuer-id", "-i", help="Issuer ID"),
    key_id: str | None = typer.Option(None, "--key-id", "-k", help="Key ID"),
    key_path: Path | None = typer.Option(None, "--key-path", "-p", help="Path to .p8 file"),
) -> None:
    """Configure authentication credentials.

    Interactive setup if no options provided.
    """
    if not all([issuer_id, key_id, key_path]):
        console.print(
            Panel(
                "[bold]App Store Connect API Authentication[/bold]\n\n"
                "Get your credentials from:\n"
                "[link]https://appstoreconnect.apple.com/access/integrations/api[/link]\n\n"
                "You'll need:\n"
                "  1. Issuer ID (UUID format)\n"
                "  2. Key ID (10 characters)\n"
                "  3. Private key file (.p8)",
                title="Setup",
            )
        )
        console.print()

        issuer_id = issuer_id or Prompt.ask("[bold]Issuer ID[/bold]")
        key_id = key_id or Prompt.ask("[bold]Key ID[/bold]")
        key_path_str = Prompt.ask(
            "[bold]Path to .p8 file[/bold]",
            default="~/.config/asc-cli/AuthKey.p8",
        )
        key_path = Path(key_path_str).expanduser()

    assert issuer_id and key_id and key_path

    if not key_path.exists():
        console.print(f"[red]Error:[/red] Key file not found: {key_path}")
        raise typer.Exit(1)

    # Read and validate the key
    try:
        private_key = key_path.read_text()
        if "BEGIN" not in private_key or "PRIVATE KEY" not in private_key:
            console.print("[red]Error:[/red] Invalid private key format")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Cannot read key file: {e}")
        raise typer.Exit(1)

    # Create credentials and test
    creds = Credentials(issuer_id=issuer_id, key_id=key_id, private_key=private_key)

    console.print("\n[dim]Testing authentication...[/dim]")

    auth = AuthManager(creds)
    try:
        # Just generate a token to verify the key works
        _ = auth.token
        console.print("[green]Authentication successful![/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] Authentication failed: {e}")
        raise typer.Exit(1)

    # Save credentials
    creds.save(key_path)
    console.print(f"\n[dim]Credentials saved to {CONFIG_DIR}[/dim]")


@app.command()
def status() -> None:
    """Check authentication status."""
    auth = AuthManager.auto()

    if auth.is_authenticated:
        console.print("[green]Authenticated[/green]")

        # Test by generating a token
        try:
            _ = auth.token
            console.print("[dim]Token generation: OK[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Token generation failed: {e}")
    else:
        console.print("[red]Not authenticated[/red]")
        console.print("\nRun [bold]asc auth login[/bold] to configure credentials.")


@app.command()
def logout() -> None:
    """Remove stored credentials."""
    from asc_cli.api.auth import CREDENTIALS_FILE

    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
        console.print("[green]Credentials removed[/green]")
    else:
        console.print("[dim]No stored credentials found[/dim]")


@app.command()
def test() -> None:
    """Test API connection by listing apps."""
    from asc_cli.api.client import AppStoreConnectClient

    async def _test() -> None:
        client = AppStoreConnectClient()
        try:
            apps = await client.list_apps()
            console.print(f"[green]Connection successful![/green] Found {len(apps)} app(s)")
            for app in apps[:5]:
                name = app.get("attributes", {}).get("name", "Unknown")
                bundle_id = app.get("attributes", {}).get("bundleId", "Unknown")
                console.print(f"  [dim]-[/dim] {name} ({bundle_id})")
            if len(apps) > 5:
                console.print(f"  [dim]... and {len(apps) - 5} more[/dim]")
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        finally:
            await client.close()

    asyncio.run(_test())
