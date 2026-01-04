"""Tests for subscription commands and utilities."""

import re

import pytest
from typer.testing import CliRunner

from asc_cli.cli import app
from asc_cli.commands.subscriptions import parse_duration


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


class TestParseDuration:
    """Tests for the parse_duration function."""

    def test_three_days(self) -> None:
        """Test parsing 3 days duration."""
        duration, periods = parse_duration("3d")
        assert duration == "THREE_DAYS"
        assert periods == 1

    def test_one_week(self) -> None:
        """Test parsing 1 week duration."""
        duration, periods = parse_duration("1w")
        assert duration == "ONE_WEEK"
        assert periods == 1

    def test_two_weeks(self) -> None:
        """Test parsing 2 weeks duration."""
        duration, periods = parse_duration("2w")
        assert duration == "TWO_WEEKS"
        assert periods == 1

    def test_one_month(self) -> None:
        """Test parsing 1 month duration."""
        duration, periods = parse_duration("1m")
        assert duration == "ONE_MONTH"
        assert periods == 1

    def test_two_months(self) -> None:
        """Test parsing 2 months duration."""
        duration, periods = parse_duration("2m")
        assert duration == "TWO_MONTHS"
        assert periods == 1

    def test_three_months(self) -> None:
        """Test parsing 3 months as 3 periods of 1 month."""
        duration, periods = parse_duration("3m")
        assert duration == "ONE_MONTH"
        assert periods == 3

    def test_six_months(self) -> None:
        """Test parsing 6 months as 6 periods of 1 month."""
        duration, periods = parse_duration("6m")
        assert duration == "ONE_MONTH"
        assert periods == 6

    def test_one_year(self) -> None:
        """Test parsing 1 year duration."""
        duration, periods = parse_duration("1y")
        assert duration == "ONE_YEAR"
        assert periods == 1

    def test_case_insensitive(self) -> None:
        """Test that parsing is case insensitive."""
        duration, periods = parse_duration("1M")
        assert duration == "ONE_MONTH"
        assert periods == 1

        duration, periods = parse_duration("1W")
        assert duration == "ONE_WEEK"
        assert periods == 1

    def test_invalid_format(self) -> None:
        """Test that invalid formats raise ValueError."""
        with pytest.raises(ValueError, match="Invalid duration format"):
            parse_duration("invalid")

    def test_invalid_days(self) -> None:
        """Test that invalid day values raise ValueError."""
        with pytest.raises(ValueError, match="Only 3d is supported"):
            parse_duration("5d")

    def test_invalid_weeks(self) -> None:
        """Test that invalid week values raise ValueError."""
        with pytest.raises(ValueError, match="Only 1w or 2w supported"):
            parse_duration("3w")

    def test_invalid_months(self) -> None:
        """Test that invalid month values raise ValueError."""
        with pytest.raises(ValueError, match="Only 1m, 2m, 3m, 6m supported"):
            parse_duration("4m")

    def test_invalid_years(self) -> None:
        """Test that invalid year values raise ValueError."""
        with pytest.raises(ValueError, match="Only 1y supported"):
            parse_duration("2y")


class TestSubscriptionsCliHelp:
    """Tests for subscriptions CLI help and argument parsing."""

    runner = CliRunner()

    def test_subscriptions_help(self) -> None:
        """Test subscriptions command shows help."""
        result = self.runner.invoke(app, ["subscriptions", "--help"])
        assert result.exit_code == 0
        assert "Manage subscriptions and pricing" in result.output

    def test_subscriptions_list_help(self) -> None:
        """Test subscriptions list command shows help."""
        result = self.runner.invoke(app, ["subscriptions", "list", "--help"])
        assert result.exit_code == 0
        assert "BUNDLE_ID" in result.output

    def test_subscriptions_check_help(self) -> None:
        """Test subscriptions check command shows help."""
        result = self.runner.invoke(app, ["subscriptions", "check", "--help"])
        assert result.exit_code == 0
        assert "Check subscription readiness" in result.output
        assert "BUNDLE_ID" in result.output

    def test_subscriptions_pricing_help(self) -> None:
        """Test subscriptions pricing command shows help."""
        result = self.runner.invoke(app, ["subscriptions", "pricing", "--help"])
        assert result.exit_code == 0
        assert "Manage subscription pricing" in result.output

    def test_subscriptions_pricing_list_help(self) -> None:
        """Test subscriptions pricing list command shows help."""
        result = self.runner.invoke(app, ["subscriptions", "pricing", "list", "--help"])
        assert result.exit_code == 0
        assert "SUBSCRIPTION_ID" in result.output

    def test_subscriptions_pricing_set_help(self) -> None:
        """Test subscriptions pricing set command shows help."""
        result = self.runner.invoke(app, ["subscriptions", "pricing", "set", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--price" in output or "-p" in output  # May use short form
        assert "--dry-run" in output
        assert "--territory" in output or "-t" in output

    def test_subscriptions_offers_help(self) -> None:
        """Test subscriptions offers command shows help."""
        result = self.runner.invoke(app, ["subscriptions", "offers", "--help"])
        assert result.exit_code == 0
        assert "introductory and promotional offers" in result.output

    def test_subscriptions_offers_create_help(self) -> None:
        """Test subscriptions offers create command shows help."""
        result = self.runner.invoke(app, ["subscriptions", "offers", "create", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "--type" in output or "-t" in output
        assert "--duration" in output or "-d" in output
        assert "--price" in output or "-p" in output
        assert "--all" in output or "-a" in output

    def test_subscriptions_offers_delete_help(self) -> None:
        """Test subscriptions offers delete command shows help."""
        result = self.runner.invoke(app, ["subscriptions", "offers", "delete", "--help"])
        assert result.exit_code == 0
        output = strip_ansi(result.output)
        assert "OFFER_ID" in output or "offer_id" in output
        assert "--force" in output or "-f" in output

    def test_subscriptions_list_missing_argument(self) -> None:
        """Test subscriptions list requires bundle_id argument."""
        result = self.runner.invoke(app, ["subscriptions", "list"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output

    def test_subscriptions_check_missing_argument(self) -> None:
        """Test subscriptions check requires bundle_id argument."""
        result = self.runner.invoke(app, ["subscriptions", "check"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output
