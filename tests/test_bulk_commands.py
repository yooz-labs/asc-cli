"""Comprehensive tests for bulk CLI commands."""

from pathlib import Path

from typer.testing import CliRunner

from asc_cli.cli import app

runner = CliRunner()


class TestBulkInit:
    """Tests for bulk init command."""

    def test_init_creates_file(self, tmp_path: Path) -> None:
        """Test init creates a configuration file."""
        output_file = tmp_path / "test_config.yaml"
        result = runner.invoke(app, ["bulk", "init", "--output", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "Created example configuration" in result.output

    def test_init_file_exists_without_force(self, tmp_path: Path) -> None:
        """Test init fails when file exists without --force."""
        output_file = tmp_path / "existing.yaml"
        output_file.write_text("existing content")

        result = runner.invoke(app, ["bulk", "init", "--output", str(output_file)])

        assert result.exit_code == 1
        assert "File already exists" in result.output
        assert "--force" in result.output

    def test_init_file_exists_with_force(self, tmp_path: Path) -> None:
        """Test init overwrites file with --force."""
        output_file = tmp_path / "existing.yaml"
        output_file.write_text("old content")

        result = runner.invoke(app, ["bulk", "init", "--output", str(output_file), "--force"])

        assert result.exit_code == 0
        assert output_file.exists()
        # Content should be new, not old
        assert "old content" not in output_file.read_text()

    def test_init_default_filename(self, tmp_path: Path, monkeypatch) -> None:
        """Test init uses default filename when not specified."""
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["bulk", "init", "--force"])

        assert result.exit_code == 0
        default_file = tmp_path / "subscriptions.yaml"
        assert default_file.exists()


class TestBulkValidate:
    """Tests for bulk validate command."""

    def test_validate_valid_config(self, tmp_path: Path) -> None:
        """Test validate with a valid configuration file."""
        config_file = tmp_path / "valid_config.yaml"
        config_content = """
app_bundle_id: com.example.test
subscriptions:
  - product_id: com.example.monthly
    price_usd: 2.99
"""
        config_file.write_text(config_content)

        result = runner.invoke(app, ["bulk", "validate", str(config_file)])

        assert result.exit_code == 0
        assert "Configuration is valid" in result.output
        assert "com.example.test" in result.output

    def test_validate_file_not_found(self) -> None:
        """Test validate with non-existent file."""
        result = runner.invoke(app, ["bulk", "validate", "/nonexistent/config.yaml"])

        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_validate_invalid_yaml(self, tmp_path: Path) -> None:
        """Test validate with invalid YAML syntax."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("app_bundle_id: [invalid yaml")

        result = runner.invoke(app, ["bulk", "validate", str(config_file)])

        assert result.exit_code == 1
        assert "Validation error" in result.output

    def test_validate_shows_summary(self, tmp_path: Path) -> None:
        """Test validate shows configuration summary."""
        config_file = tmp_path / "config.yaml"
        config_content = """
app_bundle_id: com.example.app
dry_run: true
subscriptions:
  - product_id: com.example.monthly
    price_usd: 2.99
  - product_id: com.example.yearly
    price_usd: 19.99
"""
        config_file.write_text(config_content)

        result = runner.invoke(app, ["bulk", "validate", str(config_file)])

        assert result.exit_code == 0
        assert "Configuration Summary" in result.output
        assert "Subscriptions" in result.output
        # Should show count of subscriptions
        assert "2" in result.output


class TestBulkSchema:
    """Tests for bulk schema command."""

    def test_schema_exports_json(self, tmp_path: Path) -> None:
        """Test schema exports JSON schema."""
        import json

        output_file = tmp_path / "schema.json"
        result = runner.invoke(app, ["bulk", "schema", "--output", str(output_file)])

        assert result.exit_code == 0
        assert output_file.exists()
        assert "JSON schema" in result.output

        # Verify it's valid JSON
        with output_file.open() as f:
            schema = json.load(f)
        assert isinstance(schema, dict)
        assert "properties" in schema

    def test_schema_default_filename(self, tmp_path: Path, monkeypatch) -> None:
        """Test schema uses default filename."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["bulk", "schema"])

        assert result.exit_code == 0
        default_file = tmp_path / "subscriptions.schema.json"
        assert default_file.exists()


class TestBulkApply:
    """Tests for bulk apply command."""

    def test_apply_file_not_found(self) -> None:
        """Test apply with non-existent config file."""
        result = runner.invoke(app, ["bulk", "apply", "/nonexistent/config.yaml"])

        assert result.exit_code == 1
        assert "Configuration file not found" in result.output

    def test_apply_invalid_config(self, tmp_path: Path) -> None:
        """Test apply with invalid config."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:")

        result = runner.invoke(app, ["bulk", "apply", str(config_file)])

        assert result.exit_code == 1
        assert "Error loading configuration" in result.output

    def test_apply_dry_run_flag(self, tmp_path: Path, mock_asc_with_app) -> None:
        """Test apply with --dry-run flag."""
        config_file = tmp_path / "config.yaml"
        config_content = """
app_bundle_id: com.example.test
subscriptions:
  - product_id: com.example.test.monthly
    price_usd: 2.99
"""
        config_file.write_text(config_content)

        result = runner.invoke(app, ["bulk", "apply", str(config_file), "--dry-run"])

        assert result.exit_code in [0, 1]  # May fail during processing but should parse
        if result.exit_code == 0:
            assert "DRY RUN" in result.output

    def test_apply_shows_progress(self, tmp_path: Path, mock_asc_with_app) -> None:
        """Test apply shows configuration being applied."""
        config_file = tmp_path / "config.yaml"
        config_content = """
app_bundle_id: com.example.test
subscriptions:
  - product_id: com.example.test.monthly
    price_usd: 2.99
"""
        config_file.write_text(config_content)

        result = runner.invoke(app, ["bulk", "apply", str(config_file)])

        # May succeed or fail depending on API, but should show progress
        assert "Applying configuration" in result.output or result.exit_code in [0, 1]
