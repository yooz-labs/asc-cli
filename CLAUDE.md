# asc-cli - App Store Connect CLI

## Project Overview

**Product:** Command-line interface for Apple App Store Connect API
**Purpose:** Manage subscriptions, pricing, TestFlight, and apps from the terminal
**Version:** 0.1.0
**Status:** Phase 1 - Foundation (Core infrastructure complete)

asc-cli brings App Store Connect to your terminal:
- Subscription management with bulk pricing across 175 territories
- TestFlight build and tester management
- Introductory and promotional offer configuration
- YAML-based bulk operations for reproducible configurations

## Tech Stack

- **Language:** Python 3.10+
- **CLI Framework:** Typer with Rich for terminal UI
- **HTTP Client:** httpx (async-capable)
- **Authentication:** PyJWT for App Store Connect API tokens
- **Configuration:** Pydantic for validation, PyYAML for config files
- **Linting/Formatting:** ruff with strict rules
- **Type Checking:** mypy (strict mode)
- **Testing:** pytest with coverage

## Environment Setup

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
├── CLAUDE.md              # This file
├── plan.md                # Implementation roadmap
├── README.md              # User documentation
├── pyproject.toml         # Project configuration
├── .context/              # Development context
│   ├── plan.md            # Current phase tasks
│   ├── ideas.md           # Design decisions
│   ├── research.md        # API exploration notes
│   └── scratch_history.md # Failed attempts
├── .rules/                # Coding standards
│   ├── git.md             # Commit conventions
│   ├── python.md          # Python standards
│   ├── testing.md         # NO MOCKS policy
│   ├── documentation.md   # Doc standards
│   ├── ci_cd.md           # Pipeline setup
│   ├── code_review.md     # PR review process
│   ├── self_improve.md    # Rule evolution
│   └── serena_mcp.md      # Code intelligence
├── src/asc_cli/           # Source code
│   ├── __init__.py
│   ├── cli.py             # Typer app and commands
│   ├── auth.py            # JWT token generation
│   ├── client.py          # API client
│   └── commands/          # Command modules
└── tests/                 # Test suite
```

## Serena MCP for Code Intelligence

Use Serena MCP tools for efficient code exploration and editing:
- `get_symbols_overview` - Get file structure before reading
- `find_symbol` - Search for classes, methods, functions
- `find_referencing_symbols` - Find usages of a symbol
- `replace_symbol_body` - Edit entire methods/functions
- `search_for_pattern` - Flexible regex search across codebase

Prefer symbolic tools over reading entire files when possible.

## Development Workflow

1. **Check context:** Review .context/plan.md for current tasks
2. **Understand deeply:** Check .context/ideas.md for design decisions
3. **Research if needed:** Update .context/research.md with findings
4. **Branch:** `git checkout -b feature/short-description`
5. **Code:** Follow patterns in .rules/python.md
6. **Test:** Real data only, NO mocks (see .rules/testing.md)
7. **Document failures:** Log in .context/scratch_history.md immediately
8. **Commit:** Atomic, <50 chars, no emojis
9. **PR:** Create with `gh pr create`, then run code review

## Core Principles

### [CRITICAL] NO MOCKS Policy
- Use real API responses or skip tests entirely
- For API testing: use recorded responses or sandbox environment
- Ask for sample data or test credentials if needed
**Details:** .rules/testing.md

### Git Standards
- Atomic commits, focused changes
- Messages <50 chars, no emojis
- Feature branches for all work
- No Co-Authored-By headers
**Details:** .rules/git.md

### Code Quality
- Type hints on all public functions (mypy strict)
- ruff check/format before commit
- Pre-commit hooks enforce standards
**Details:** .rules/python.md

## Quick Commands

```bash
# Run tests (real data only)
pytest tests/ --cov

# Format and lint
ruff check --fix . && ruff format .

# Type check
mypy src/

# Build package
python -m build

# Run CLI
asc auth status
asc apps list
asc subscriptions list
```

## App Store Connect API

### Authentication
```bash
# Set credentials (stored in ~/.config/asc-cli/)
export ASC_ISSUER_ID="your-issuer-id"
export ASC_KEY_ID="your-key-id"
export ASC_PRIVATE_KEY_PATH="~/.asc/AuthKey_XXXXX.p8"
```

### Key Endpoints
- `/v1/apps` - App management
- `/v1/subscriptions` - Subscription CRUD
- `/v1/subscriptionGroups` - Subscription groups
- `/v1/subscriptionPrices` - Pricing
- `/v1/subscriptionPricePoints` - Price point lookup
- `/v1/subscriptionIntroductoryOffers` - Intro offers
- `/v1/builds` - TestFlight builds
- `/v1/betaGroups` - Beta groups
- `/v1/betaTesters` - Tester management

## Current Phase

**Phase 1: Foundation** (Current)
- [x] Project structure with uv/ruff/mypy
- [x] Typer CLI framework setup
- [x] Authentication module (JWT token generation)
- [x] Base API client with httpx
- [x] Credential storage
- [x] `asc auth login/status/logout/test`
- [x] `asc apps list/info`
- [x] `asc subscriptions list` (basic)

**Phase 2: Subscriptions & Pricing** (Next)
- [ ] `asc subscriptions pricing list/set`
- [ ] `asc subscriptions offers list/create/delete`
- [ ] Bulk pricing from YAML
- [ ] Territory management

See plan.md for full roadmap.

## References

- **App Store Connect API:** https://developer.apple.com/documentation/appstoreconnectapi
- **API Reference:** https://developer.apple.com/documentation/appstoreconnectapi/app_store
- **Yooz Whisper (related):** ../yooz-whisper/
- **Product Research:** /Users/yahya/Documents/git/yooz/yooz/product-research/

## Rules Reference

| Rule File | Purpose |
|-----------|---------|
| `.rules/testing.md` | NO MOCKS policy, real data testing |
| `.rules/python.md` | Style, type hints, structure |
| `.rules/git.md` | Commits, branches, PRs |
| `.rules/documentation.md` | MkDocs, docstrings |
| `.rules/ci_cd.md` | GitHub Actions |
| `.rules/code_review.md` | PR review toolkit |
| `.rules/self_improve.md` | Rule evolution |
| `.rules/serena_mcp.md` | Code intelligence |

---

*Last Updated: January 4, 2026*
