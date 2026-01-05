"""Tests for configuration schema validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from asc_cli.config.schema import (
    IntroductoryOffer,
    OfferType,
    SubscriptionConfig,
    SubscriptionPeriod,
    SubscriptionsConfig,
)


class TestSubscriptionPeriod:
    """Tests for SubscriptionPeriod enum."""

    def test_all_periods_defined(self) -> None:
        """Test all expected periods are defined."""
        periods = [p.value for p in SubscriptionPeriod]
        assert "1w" in periods
        assert "1m" in periods
        assert "2m" in periods
        assert "3m" in periods
        assert "6m" in periods
        assert "1y" in periods

    def test_to_api_value_one_week(self) -> None:
        """Test ONE_WEEK converts to API value."""
        assert SubscriptionPeriod.ONE_WEEK.to_api_value() == "ONE_WEEK"

    def test_to_api_value_one_month(self) -> None:
        """Test ONE_MONTH converts to API value."""
        assert SubscriptionPeriod.ONE_MONTH.to_api_value() == "ONE_MONTH"

    def test_to_api_value_one_year(self) -> None:
        """Test ONE_YEAR converts to API value."""
        assert SubscriptionPeriod.ONE_YEAR.to_api_value() == "ONE_YEAR"


class TestOfferType:
    """Tests for OfferType enum."""

    def test_all_offer_types_defined(self) -> None:
        """Test all expected offer types are defined."""
        types = [t.value for t in OfferType]
        assert "free-trial" in types
        assert "pay-as-you-go" in types
        assert "pay-up-front" in types


class TestIntroductoryOffer:
    """Tests for IntroductoryOffer model."""

    def test_free_trial_valid(self) -> None:
        """Test valid free trial offer."""
        offer = IntroductoryOffer(type=OfferType.FREE_TRIAL, duration="2w")
        assert offer.type == OfferType.FREE_TRIAL
        assert offer.duration == "2w"
        assert offer.price_usd is None
        assert offer.territories == "all"

    def test_pay_as_you_go_with_price(self) -> None:
        """Test pay-as-you-go offer with price."""
        offer = IntroductoryOffer(
            type=OfferType.PAY_AS_YOU_GO,
            duration="3m",
            price_usd=1.99,
        )
        assert offer.type == OfferType.PAY_AS_YOU_GO
        assert offer.price_usd == 1.99

    def test_pay_up_front_with_price(self) -> None:
        """Test pay-up-front offer with price."""
        offer = IntroductoryOffer(
            type=OfferType.PAY_UP_FRONT,
            duration="6m",
            price_usd=9.99,
        )
        assert offer.type == OfferType.PAY_UP_FRONT
        assert offer.price_usd == 9.99

    def test_pay_as_you_go_requires_price(self) -> None:
        """Test that pay-as-you-go offer requires price."""
        with pytest.raises(ValueError, match="price_usd is required"):
            IntroductoryOffer(type=OfferType.PAY_AS_YOU_GO, duration="3m")

    def test_pay_up_front_requires_price(self) -> None:
        """Test that pay-up-front offer requires price."""
        with pytest.raises(ValueError, match="price_usd is required"):
            IntroductoryOffer(type=OfferType.PAY_UP_FRONT, duration="3m")

    def test_invalid_duration_format(self) -> None:
        """Test that invalid duration format raises error."""
        with pytest.raises(ValidationError):
            IntroductoryOffer(type=OfferType.FREE_TRIAL, duration="invalid")

    def test_specific_territories(self) -> None:
        """Test offer with specific territories."""
        offer = IntroductoryOffer(
            type=OfferType.FREE_TRIAL,
            duration="1w",
            territories=["USA", "GBR", "CAN"],
        )
        assert offer.territories == ["USA", "GBR", "CAN"]

    def test_negative_price_rejected(self) -> None:
        """Test that negative price is rejected."""
        with pytest.raises(ValidationError):
            IntroductoryOffer(
                type=OfferType.PAY_AS_YOU_GO,
                duration="1m",
                price_usd=-1.0,
            )


class TestSubscriptionConfig:
    """Tests for SubscriptionConfig model."""

    def test_minimal_config(self) -> None:
        """Test minimal subscription config."""
        config = SubscriptionConfig(
            product_id="com.example.pro.monthly",
            price_usd=2.99,
        )
        assert config.product_id == "com.example.pro.monthly"
        assert config.price_usd == 2.99
        assert config.territories == "all"
        assert config.offers == []

    def test_with_period(self) -> None:
        """Test subscription config with period."""
        config = SubscriptionConfig(
            product_id="com.example.pro.monthly",
            price_usd=2.99,
            period=SubscriptionPeriod.ONE_MONTH,
        )
        assert config.period == SubscriptionPeriod.ONE_MONTH

    def test_with_offers(self) -> None:
        """Test subscription config with offers."""
        config = SubscriptionConfig(
            product_id="com.example.pro.monthly",
            price_usd=2.99,
            offers=[
                IntroductoryOffer(type=OfferType.FREE_TRIAL, duration="2w"),
            ],
        )
        assert len(config.offers) == 1
        assert config.offers[0].type == OfferType.FREE_TRIAL

    def test_with_specific_territories(self) -> None:
        """Test subscription config with specific territories."""
        config = SubscriptionConfig(
            product_id="com.example.pro.monthly",
            price_usd=2.99,
            territories=["USA", "GBR"],
        )
        assert config.territories == ["USA", "GBR"]


class TestSubscriptionsConfig:
    """Tests for SubscriptionsConfig model."""

    def test_minimal_config(self) -> None:
        """Test minimal subscriptions config."""
        config = SubscriptionsConfig(
            app_bundle_id="com.example.app",
            subscriptions=[
                SubscriptionConfig(
                    product_id="com.example.pro",
                    price_usd=2.99,
                ),
            ],
        )
        assert config.app_bundle_id == "com.example.app"
        assert len(config.subscriptions) == 1

    def test_from_yaml_file(self, tmp_path: Path) -> None:
        """Test parsing config from YAML file."""
        yaml_content = """
app_bundle_id: com.example.app
subscriptions:
  - product_id: com.example.pro.monthly
    price_usd: 2.99
    territories: all
"""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(yaml_content)

        config = SubscriptionsConfig.from_yaml(yaml_file)
        assert config.app_bundle_id == "com.example.app"
        assert len(config.subscriptions) == 1
        assert config.subscriptions[0].product_id == "com.example.pro.monthly"

    def test_from_yaml_with_offers(self, tmp_path: Path) -> None:
        """Test parsing config with offers from YAML."""
        yaml_content = """
app_bundle_id: com.example.app
subscriptions:
  - product_id: com.example.pro.monthly
    price_usd: 2.99
    offers:
      - type: free-trial
        duration: 2w
"""
        yaml_file = tmp_path / "config.yaml"
        yaml_file.write_text(yaml_content)

        config = SubscriptionsConfig.from_yaml(yaml_file)
        assert len(config.subscriptions[0].offers) == 1
        assert config.subscriptions[0].offers[0].type == OfferType.FREE_TRIAL

    def test_from_yaml_file_not_found(self, tmp_path: Path) -> None:
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            SubscriptionsConfig.from_yaml(tmp_path / "nonexistent.yaml")

    def test_to_yaml_roundtrip(self, tmp_path: Path) -> None:
        """Test that config can be serialized and parsed back."""
        original = SubscriptionsConfig(
            app_bundle_id="com.example.app",
            subscriptions=[
                SubscriptionConfig(
                    product_id="com.example.pro",
                    price_usd=2.99,
                    offers=[
                        IntroductoryOffer(type=OfferType.FREE_TRIAL, duration="1w"),
                    ],
                ),
            ],
        )
        yaml_file = tmp_path / "config.yaml"
        original.to_yaml(yaml_file)
        parsed = SubscriptionsConfig.from_yaml(yaml_file)

        assert parsed.app_bundle_id == original.app_bundle_id
        assert len(parsed.subscriptions) == len(original.subscriptions)
        assert parsed.subscriptions[0].product_id == original.subscriptions[0].product_id


class TestSchemaHelpers:
    """Tests for schema helper functions."""

    def test_generate_json_schema(self) -> None:
        """Test generating JSON schema."""
        schema = SubscriptionsConfig.generate_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "app_bundle_id" in schema["properties"]
        assert "subscriptions" in schema["properties"]

    def test_write_json_schema(self, tmp_path: Path) -> None:
        """Test writing JSON schema to file."""
        import json

        schema_file = tmp_path / "schema.json"
        SubscriptionsConfig.write_json_schema(schema_file)

        assert schema_file.exists()

        with schema_file.open() as f:
            schema = json.load(f)

        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_generate_example_config_without_path(self) -> None:
        """Test generating example config as string."""
        from asc_cli.config.schema import generate_example_config

        example = generate_example_config()

        assert isinstance(example, str)
        assert "app_bundle_id" in example
        assert "subscriptions" in example
        assert "product_id" in example

    def test_generate_example_config_with_path(self, tmp_path: Path) -> None:
        """Test generating example config and writing to file."""
        from asc_cli.config.schema import generate_example_config

        example_file = tmp_path / "example.yaml"
        result = generate_example_config(path=example_file)

        assert example_file.exists()
        assert isinstance(result, str)

        content = example_file.read_text()
        assert content == result
        assert "app_bundle_id" in content
