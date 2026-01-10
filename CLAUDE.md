# asc-cli - App Store Connect CLI

## Project Overview

**Product:** Command-line interface for Apple App Store Connect API
**Purpose:** Manage subscriptions, pricing, TestFlight, and apps from the terminal
**Version:** 0.1.0
**Status:** Phase 1 - Foundation (Core infrastructure complete)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| CLI Framework | Typer + Rich |
| HTTP Client | httpx (async) |
| Authentication | PyJWT |
| Configuration | Pydantic + PyYAML |
| Linting | ruff (strict) |
| Type Checking | mypy (strict) |

## Quick Start

```bash
# Use conda environment
source ~/miniconda3/etc/profile.d/conda.sh && conda activate yooz

# Install in development mode
pip install -e ".[dev]"

# Run CLI
asc --help
```

## Project Structure

```
asc-cli/
├── src/asc_cli/
│   ├── cli.py             # Typer app and commands
│   ├── auth.py            # JWT token generation
│   ├── client.py          # API client
│   └── commands/          # Command modules
├── tests/                 # Test suite (NO MOCKS)
├── .context/              # plan.md, ideas.md, research.md
└── .rules/                # Coding standards
```

## App Store Connect API

### Authentication
```bash
export ASC_ISSUER_ID="your-issuer-id"
export ASC_KEY_ID="your-key-id"
export ASC_PRIVATE_KEY_PATH="~/.asc/AuthKey_XXXXX.p8"
```

### Key Endpoints
| Endpoint | Purpose |
|----------|---------|
| `/v1/apps` | App management |
| `/v1/subscriptions` | Subscription CRUD |
| `/v1/subscriptionGroups` | Subscription groups |
| `/v1/subscriptionPrices` | Pricing |
| `/v1/builds` | TestFlight builds |
| `/v1/betaGroups` | Beta groups |
| `/v1/betaTesters` | Tester management |

## Quick Commands

```bash
# Run tests (real data only)
pytest tests/ --cov

# Format and lint
ruff check --fix . && ruff format .

# Type check
mypy src/

# CLI commands
asc auth status
asc apps list
asc subscriptions list
```

## Current Phase

**Phase 1: Foundation** (Current)
- [x] Project structure with uv/ruff/mypy
- [x] Typer CLI framework
- [x] Authentication module (JWT)
- [x] Base API client (httpx)
- [x] `asc auth login/status/logout/test`
- [x] `asc apps list/info`
- [x] `asc subscriptions list` (basic)

**Phase 2: Subscriptions & Pricing** (Next)
- [ ] `asc subscriptions pricing list/set`
- [ ] Bulk pricing from YAML
- [ ] Territory management

## References

- **API Docs:** https://developer.apple.com/documentation/appstoreconnectapi
- **Yooz Whisper:** ../yooz-whisper/
- **Product Research:** /Users/yahya/Documents/git/yooz/yooz/product-research/

---

*Part of the Yooz ecosystem*
