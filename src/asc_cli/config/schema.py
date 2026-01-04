"""Pydantic schema for subscription configuration files.

This module defines the schema for YAML configuration files that can be used
to configure subscriptions, pricing, and offers in bulk.

Example YAML:

```yaml
# subscriptions.yaml
app_bundle_id: live.yooz.whisper

subscriptions:
  - product_id: live.yooz.whisper.pro.monthly
    name: Pro Monthly
    price_usd: 2.99
    territories: all  # or list specific ones
    offers:
      - type: free-trial
        duration: 2w
      - type: pay-as-you-go
        duration: 3m
        price_usd: 1.99

  - product_id: live.yooz.whisper.pro.yearly
    name: Pro Yearly
    price_usd: 29.99
    territories: all
    offers:
      - type: free-trial
        duration: 1w
```
"""

from enum import Enum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator


class SubscriptionPeriod(str, Enum):
    """Billing periods for subscriptions."""

    ONE_WEEK = "1w"
    ONE_MONTH = "1m"
    TWO_MONTHS = "2m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"
    ONE_YEAR = "1y"

    def to_api_value(self) -> str:
        """Convert to App Store Connect API value."""
        mapping = {
            "1w": "ONE_WEEK",
            "1m": "ONE_MONTH",
            "2m": "TWO_MONTHS",
            "3m": "THREE_MONTHS",
            "6m": "SIX_MONTHS",
            "1y": "ONE_YEAR",
        }
        return mapping[self.value]


class OfferType(str, Enum):
    """Types of introductory offers."""

    FREE_TRIAL = "free-trial"
    PAY_AS_YOU_GO = "pay-as-you-go"
    PAY_UP_FRONT = "pay-up-front"


class IntroductoryOffer(BaseModel):
    """Configuration for an introductory offer."""

    type: OfferType = Field(..., description="Type of offer")
    duration: str = Field(
        ...,
        description="Duration in human format: 3d, 1w, 2w, 1m, 3m, 6m, 1y",
        pattern=r"^\d+[dwmy]$",
    )
    price_usd: float | None = Field(
        None,
        description="Price in USD (required for pay-as-you-go and pay-up-front)",
        ge=0,
    )
    territories: list[str] | Literal["all"] = Field(
        "all",
        description="Territories to apply offer to, or 'all'",
    )

    @field_validator("price_usd")
    @classmethod
    def validate_price_for_type(cls, v: float | None) -> float | None:
        """Validate that paid offers have a price."""
        # Note: Cross-field validation happens in model_post_init
        return v

    def model_post_init(self, __context: object) -> None:
        """Validate after model initialization."""
        if self.type != OfferType.FREE_TRIAL and self.price_usd is None:
            raise ValueError(f"price_usd is required for {self.type.value} offers")


class SubscriptionConfig(BaseModel):
    """Configuration for a single subscription."""

    product_id: str = Field(..., description="App Store product ID")
    name: str | None = Field(None, description="Display name for the subscription")
    period: SubscriptionPeriod | None = Field(
        None,
        description="Billing period: 1w, 1m, 2m, 3m, 6m, 1y (set if not already configured)",
    )
    price_usd: float = Field(..., description="Base price in USD", ge=0)
    territories: list[str] | Literal["all"] = Field(
        "all",
        description="Territories to set pricing for, or 'all'",
    )
    equalize: bool = Field(
        True,
        description="Use Apple's price equalization for other currencies",
    )
    offers: list[IntroductoryOffer] = Field(
        default_factory=list,
        description="Introductory offers for this subscription",
    )


class SubscriptionsConfig(BaseModel):
    """Root configuration for subscription management."""

    app_bundle_id: str = Field(..., description="App bundle ID")
    subscriptions: list[SubscriptionConfig] = Field(
        ...,
        description="List of subscriptions to configure",
    )
    dry_run: bool = Field(
        False,
        description="If true, only preview changes without applying",
    )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SubscriptionsConfig":
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with path.open() as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)

    def to_yaml(self, path: str | Path) -> None:
        """Write configuration to a YAML file."""
        path = Path(path)
        with path.open("w") as f:
            yaml.dump(
                self.model_dump(mode="json"),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

    @classmethod
    def generate_json_schema(cls) -> dict[str, Any]:
        """Generate JSON schema for the configuration."""
        return cls.model_json_schema()

    @classmethod
    def write_json_schema(cls, path: str | Path) -> None:
        """Write JSON schema to a file."""
        import json

        path = Path(path)
        with path.open("w") as f:
            json.dump(cls.generate_json_schema(), f, indent=2)


# Example configuration template
EXAMPLE_CONFIG = """# asc-cli Subscription Configuration
# Schema: https://github.com/yooz-labs/asc-cli/blob/main/schema/subscriptions.schema.json

app_bundle_id: com.example.myapp

# Set to true to preview changes without applying
dry_run: false

subscriptions:
  # Pro Monthly subscription
  - product_id: com.example.myapp.pro.monthly
    name: Pro Monthly
    period: 1m        # Billing period: 1w, 1m, 2m, 3m, 6m, 1y
    price_usd: 2.99
    territories: all  # Apply to all 175 territories
    equalize: true    # Use Apple's automatic price equalization
    offers:
      # 2-week free trial for new subscribers
      - type: free-trial
        duration: 2w
        territories: all

      # $1.99/month for first 3 months
      - type: pay-as-you-go
        duration: 3m
        price_usd: 1.99
        territories: all

  # Pro Yearly subscription
  - product_id: com.example.myapp.pro.yearly
    name: Pro Yearly
    price_usd: 29.99
    territories: all
    equalize: true
    offers:
      # 1-week free trial
      - type: free-trial
        duration: 1w
        territories: all

  # Pro Family Monthly
  - product_id: com.example.myapp.pro.family.monthly
    name: Pro Family Monthly
    price_usd: 6.99
    territories: all
    offers:
      - type: free-trial
        duration: 2w

      # $3.99/month for first 3 months promo
      - type: pay-as-you-go
        duration: 3m
        price_usd: 3.99
"""


def generate_example_config(path: str | Path | None = None) -> str:
    """Generate an example configuration file.

    Args:
        path: If provided, write the example to this path

    Returns:
        The example configuration as a string
    """
    if path:
        path = Path(path)
        with path.open("w") as f:
            f.write(EXAMPLE_CONFIG)

    return EXAMPLE_CONFIG
