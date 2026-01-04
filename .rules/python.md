# Python Development Standards

## Version & Environment
- **Python 3.10+** minimum
- **Virtual Environment:** conda (`yooz` environment) or venv
- **Package Management:** `pip` with `pyproject.toml`

## Code Style
- **Formatter:** `ruff format` (Black-compatible)
- **Linter:** `ruff check` with aggressive fixes
- **Line Length:** 100 characters (project standard)
- **Imports:** Sorted with isort (via ruff)

## Type Hints
- **Required for:** All public functions and methods
- **Tool:** `mypy` with strict mode
- **Example:**
```python
def list_subscriptions(app_id: str, include_prices: bool = False) -> list[Subscription]:
    """List all subscriptions for an app."""
    ...
```

## Project Structure
```
asc-cli/
├── src/asc_cli/        # Source code
│   ├── __init__.py
│   ├── cli.py          # Typer app
│   ├── auth.py         # Authentication
│   ├── client.py       # API client
│   └── commands/       # Command modules
├── tests/              # Real tests only
├── pyproject.toml      # Project config
└── .gitignore
```

## Pre-commit Hook
The project uses `.pre-commit-config.yaml` with ruff and mypy.

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Common Patterns
- **Context Managers:** For resource management (files, connections)
- **Dataclasses/Pydantic:** For data structures
- **Pathlib:** For file operations (not os.path)
- **F-strings:** For string formatting
- **Typer:** For CLI commands with rich help

## Error Handling
```python
# Be specific with exceptions
try:
    response = client.get(endpoint)
except httpx.HTTPStatusError as e:
    console.print(f"[red]API error: {e.response.status_code}[/red]")
    raise typer.Exit(1)
```

## CLI Patterns (Typer)
```python
@app.command()
def list_apps(
    format: str = typer.Option("table", help="Output format"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """List all apps in App Store Connect."""
    ...
```

## Documentation
- **Docstrings:** Google style
- **Module docs:** At file top
- **Type hints:** Self-documenting code

---
*Follow PEP 8 with ruff enforcement. Real tests only.*
