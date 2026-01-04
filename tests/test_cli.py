"""Tests for CLI entry point."""

from typer.testing import CliRunner

from asc_cli import __version__
from asc_cli.cli import app

runner = CliRunner()


def test_version() -> None:
    """Test version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help() -> None:
    """Test help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "App Store Connect" in result.output


def test_auth_help() -> None:
    """Test auth subcommand help."""
    result = runner.invoke(app, ["auth", "--help"])
    assert result.exit_code == 0
    assert "login" in result.output
    assert "status" in result.output


def test_apps_help() -> None:
    """Test apps subcommand help."""
    result = runner.invoke(app, ["apps", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output


def test_subscriptions_help() -> None:
    """Test subscriptions subcommand help."""
    result = runner.invoke(app, ["subscriptions", "--help"])
    assert result.exit_code == 0
    assert "pricing" in result.output
    assert "offers" in result.output


def test_testflight_help() -> None:
    """Test testflight subcommand help."""
    result = runner.invoke(app, ["testflight", "--help"])
    assert result.exit_code == 0
    assert "builds" in result.output
    assert "groups" in result.output
    assert "testers" in result.output
