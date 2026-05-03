# asc-cli

A command-line interface for the Apple App Store Connect API.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/github/yooz-labs/asc-cli/graph/badge.svg?token=8XGCPL63LP)](https://codecov.io/github/yooz-labs/asc-cli)

## Overview

`asc-cli` brings App Store Connect to your terminal. Manage subscriptions, pricing, TestFlight, and apps without leaving the command line. It's a generic developer utility, useful to anyone shipping iOS / macOS / tvOS / visionOS apps, not specific to Yooz.

```bash
# Configure pricing for all territories
asc subscriptions pricing set --product pro.monthly --price 2.99

# Add a free trial
asc subscriptions offers create --product pro.monthly --type free-trial --duration 14d

# List TestFlight builds
asc testflight builds list --app "My App"

# Submit for review
asc apps submit --app "My App" --version 1.0.0
```

## Features

- **Subscriptions** - Create, configure, and manage auto-renewable subscriptions.
- **Pricing** - Set prices across 175 territories with a single command.
- **Introductory offers** - Configure free trials, pay-as-you-go, and pay-up-front offers.
- **Promotional offers** - Manage promotional pricing campaigns.
- **TestFlight** - Manage builds, beta groups, and testers.
- **App management** - Submit apps, manage versions, and more.
- **Bulk operations** - Apply changes across multiple products / territories from YAML.

## Installation

### pip

```bash
pip install asc-cli
```

### Homebrew (coming soon)

```bash
brew install yooz-labs/tap/asc-cli
```

### From source

```bash
git clone https://github.com/yooz-labs/asc-cli.git
cd asc-cli
pip install -e .
```

## Quick start

### 1. Get API credentials

1. Go to [App Store Connect](https://appstoreconnect.apple.com).
2. Navigate to **Users and Access** → **Integrations** → **App Store Connect API**.
3. Generate a new key with the **Admin** or **App Manager** role.
4. Download the `.p8` private key file.
5. Note the **Key ID** and **Issuer ID**.

### 2. Configure authentication

```bash
# Interactive setup
asc auth login

# Or set environment variables
export ASC_ISSUER_ID="your-issuer-id"
export ASC_KEY_ID="your-key-id"
export ASC_PRIVATE_KEY_PATH="~/.asc/AuthKey_XXXXX.p8"
```

### 3. Start using

```bash
# List your apps
asc apps list

# Get subscription info
asc subscriptions list --app "My App"

# Set pricing
asc subscriptions pricing set --subscription "pro.monthly" --price 2.99
```

## Command reference

### Authentication

```bash
asc auth login              # Interactive authentication setup
asc auth status             # Check authentication status
asc auth logout             # Remove stored credentials
```

### Apps

```bash
asc apps list               # List all apps
asc apps info <bundle-id>   # Get app details
asc apps submit             # Submit for App Review
```

### Subscriptions

```bash
asc subscriptions list                    # List subscription groups
asc subscriptions create                  # Create a new subscription
asc subscriptions delete <id>             # Delete a subscription
asc subscriptions pricing list            # List current pricing
asc subscriptions pricing set             # Set pricing
asc subscriptions offers list             # List introductory offers
asc subscriptions offers create           # Create an offer
asc subscriptions offers delete           # Delete an offer
```

### TestFlight

```bash
asc testflight builds list                # List builds
asc testflight builds expire <id>         # Expire a build
asc testflight groups list                # List beta groups
asc testflight groups create              # Create a beta group
asc testflight testers list               # List testers
asc testflight testers add                # Add a tester
asc testflight testers remove             # Remove a tester
```

### Bulk operations

```bash
asc bulk pricing --file pricing.yaml      # Apply pricing from YAML
asc bulk offers --file offers.yaml        # Apply offers from YAML
```

## Configuration files

### Pricing configuration (pricing.yaml)

```yaml
subscriptions:
  - product_id: com.example.app.pro.monthly
    base_price: 2.99
    currency: USD
    territories: all  # or list specific ones

  - product_id: com.example.app.pro.yearly
    base_price: 29.99
    currency: USD
    territories:
      - USA
      - GBR
      - DEU
```

### Offers configuration (offers.yaml)

```yaml
introductory_offers:
  - product_id: com.example.app.pro.monthly
    type: free-trial
    duration: 14  # days
    territories: all

  - product_id: com.example.app.pro.monthly
    type: pay-as-you-go
    duration: 3  # months
    price: 1.99
    territories: all
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `ASC_ISSUER_ID` | App Store Connect Issuer ID |
| `ASC_KEY_ID` | API Key ID |
| `ASC_PRIVATE_KEY_PATH` | Path to .p8 private key file |
| `ASC_PRIVATE_KEY` | Private key contents (alternative to path) |

## Legal

This tool is not affiliated with, endorsed by, or sponsored by Apple Inc. App Store Connect is a trademark of Apple Inc.

Users are responsible for complying with Apple's [App Store Connect API Terms of Service](https://developer.apple.com/support/terms/).

## License

Licensed under the [Apache License 2.0](LICENSE.md). asc-cli is a generic developer utility; the permissive license matches the audience. The full ecosystem licensing strategy lives in [yooz-engine/LICENSING.md](https://github.com/yooz-labs/yooz-engine/blob/main/LICENSING.md).

The repository was previously distributed under BSD-3-Clause; the relicense to Apache 2.0 was made by the sole copyright holder (Yooz Labs Inc.) and applies to all versions going forward.

## Contributing

PRs welcome. Sign your commits with `Signed-off-by: Your Name <you@example.com>` (DCO style); see [`CONTRIBUTING.md`](CONTRIBUTING.md). Security issues: see [`SECURITY.md`](SECURITY.md).

---

*Maintained by [Yooz Labs](https://github.com/yooz-labs). Contact: dev@yooz.info.*
