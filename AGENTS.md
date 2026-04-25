# asc-cli — App Store Connect CLI

Project-specific agent instructions. Ecosystem-wide rules live in `../AGENTS.md`.

## Project Overview

- **Product:** CLI for the Apple App Store Connect API.
- **Purpose:** Manage subscriptions, pricing, TestFlight, and apps from the terminal.
- **Version:** 0.1.0
- **Status:** Phase 1 — Foundation (core infrastructure complete).

## Tech Stack

| Component | Tech |
|---|---|
| Language | Python 3.10+ |
| CLI framework | Typer + Rich |
| HTTP client | httpx (async) |
| Auth | PyJWT |
| Configuration | Pydantic + PyYAML |
| Lint | ruff (strict) |
| Type check | mypy (strict) |

> **Note:** the ecosystem default for type checking is `ty`. This project still uses `mypy`. Migrate when convenient.

## Quick Start

```bash
# Use UV (ecosystem default)
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run CLI
asc --help
```

> The original setup notes used conda; UV is preferred and equivalent. Use conda only if UV blocks for some reason.

## Repository Layout

```
asc-cli/
├── src/asc_cli/
│   ├── cli.py           # Typer app and commands
│   ├── auth.py          # JWT token generation
│   ├── client.py        # API client
│   └── commands/        # Command modules
├── tests/               # Test suite (NO MOCKS)
├── .context/            # plan.md, ideas.md, research.md
└── .rules/              # Coding standards
```

## App Store Connect API

### Authentication

```bash
export ASC_ISSUER_ID="your-issuer-id"
export ASC_KEY_ID="your-key-id"
export ASC_PRIVATE_KEY_PATH="~/.asc/AuthKey_XXXXX.p8"
```

### Key endpoints

| Endpoint | Purpose |
|---|---|
| `/v1/apps` | App management |
| `/v1/subscriptions` | Subscription CRUD |
| `/v1/subscriptionGroups` | Subscription groups |
| `/v1/subscriptionPrices` | Pricing |
| `/v1/builds` | TestFlight builds |
| `/v1/betaGroups` | Beta groups |
| `/v1/betaTesters` | Tester management |

## Common Commands

```bash
# Tests (real data only)
pytest tests/ --cov

# Format and lint
ruff check --fix . && ruff format .

# Type check
mypy src/

# CLI
asc auth status
asc apps list
asc subscriptions list
```

## Phases

**Phase 1 — Foundation (current):**

- [x] Project structure with UV / ruff / mypy
- [x] Typer CLI framework
- [x] Auth module (JWT)
- [x] Base API client (httpx)
- [x] `asc auth login/status/logout/test`
- [x] `asc apps list/info`
- [x] `asc subscriptions list` (basic)

**Phase 2 — Subscriptions & Pricing (next):**

- [ ] `asc subscriptions pricing list/set`
- [ ] Bulk pricing from YAML
- [ ] Territory management

## References

- API docs: https://developer.apple.com/documentation/appstoreconnectapi
- Sibling repo: `yooz-whisper/`

---

*Part of the Yooz ecosystem.*
