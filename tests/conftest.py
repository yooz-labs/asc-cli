"""Pytest configuration and fixtures.

This module provides fixtures for both simulation-based tests
and integration tests.
"""

import os

import pytest

from tests.simulation import ASCSimulator, StateManager
from tests.simulation.fixtures.apps import load_sample_app, load_whisper_app
from tests.simulation.fixtures.territories import load_territories
from tests.test_keys import get_test_credentials


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up environment variables for all tests.

    Provides test ASC credentials so AuthManager doesn't fail
    when CLI commands are tested with the simulation.

    Keys are either read from ASC_TEST_PRIVATE_KEY env var or
    generated dynamically. See tests/test_keys.py for details.
    """
    credentials = get_test_credentials()

    # Set test credentials
    for key, value in credentials.items():
        os.environ[key] = value

    yield

    # Cleanup after all tests
    for key in credentials:
        os.environ.pop(key, None)


@pytest.fixture
def asc_state() -> StateManager:
    """Fresh state manager for each test.

    Returns:
        Clean StateManager instance
    """
    state = StateManager()
    load_territories(state)
    return state


@pytest.fixture
def asc_simulator(asc_state: StateManager) -> ASCSimulator:
    """Configured API simulator with territories loaded.

    Args:
        asc_state: Pre-populated state manager

    Returns:
        ASCSimulator instance with state attached
    """
    sim = ASCSimulator()
    sim.state = asc_state
    return sim


@pytest.fixture
def mock_asc_api(asc_simulator: ASCSimulator):
    """Context manager that mocks the ASC API.

    Usage:
        def test_something(mock_asc_api):
            sim = mock_asc_api
            sim.state.add_app("app_1", "com.example.app", "My App")
            # ... test code using real client

    Yields:
        ASCSimulator instance with active mocking
    """
    with asc_simulator.mock_context():
        yield asc_simulator


@pytest.fixture
def mock_asc_with_app(asc_simulator: ASCSimulator):
    """Simulator with a pre-configured sample app.

    Creates:
        - App with ID "app_123"
        - Subscription group "group_app_123"
        - Subscription "sub_app_123" with ONE_MONTH period
        - Localization for the subscription

    Yields:
        ASCSimulator instance with app data and active mocking
    """
    load_sample_app(asc_simulator.state)
    with asc_simulator.mock_context():
        yield asc_simulator


@pytest.fixture
def mock_asc_whisper(asc_simulator: ASCSimulator):
    """Simulator configured like the Whisper app.

    Creates:
        - App matching live.yooz.whisper
        - 4 subscriptions (monthly, yearly, family variants)
        - Price points for all territories
        - Localizations

    Yields:
        ASCSimulator instance with Whisper app data and active mocking
    """
    load_whisper_app(asc_simulator.state)
    with asc_simulator.mock_context():
        yield asc_simulator


@pytest.fixture
def mock_asc_no_subscriptions(asc_simulator: ASCSimulator):
    """Simulator with app but no subscriptions.

    Useful for testing subscription creation flows.

    Yields:
        ASCSimulator instance with app but no subscriptions
    """
    load_sample_app(
        asc_simulator.state,
        with_subscriptions=False,
    )
    with asc_simulator.mock_context():
        yield asc_simulator


@pytest.fixture
def mock_asc_missing_period(asc_simulator: ASCSimulator):
    """Simulator with subscription that has no period set.

    Useful for testing error handling when period is required.

    Yields:
        ASCSimulator instance with subscription missing period
    """
    load_sample_app(
        asc_simulator.state,
        subscription_period=None,  # Period not set
    )
    with asc_simulator.mock_context():
        yield asc_simulator


@pytest.fixture
def mock_asc_with_testflight(asc_simulator: ASCSimulator):
    """Simulator with TestFlight data: builds, groups, testers.

    Creates:
        - App with ID "app_123"
        - Multiple builds (0.2.5, 0.2.6, 0.2.7)
        - Beta groups (internal, external)
        - Beta testers
        - Build localizations (What's New)

    Yields:
        ASCSimulator instance with TestFlight data and active mocking
    """
    state = asc_simulator.state

    # Add app
    state.add_app("app_123", "com.example.test", "Test App", "test_sku")

    # Add builds (version is CFBundleVersion = build number for API filtering)
    state.add_build(
        "build_1",
        "app_123",
        version="10",  # Build number - used by API filter[version]
        build_number="10",
        processing_state="VALID",
        uploaded_date="2026-01-01T10:00:00.000Z",
    )
    state.add_build(
        "build_2",
        "app_123",
        version="11",  # Build number - used by API filter[version]
        build_number="11",
        processing_state="VALID",
        uploaded_date="2026-01-03T10:00:00.000Z",
    )
    state.add_build(
        "build_3",
        "app_123",
        version="13",  # Build number - used by API filter[version]
        build_number="13",
        processing_state="VALID",
        uploaded_date="2026-01-05T10:00:00.000Z",
    )

    # Add beta groups
    state.add_beta_group(
        "group_internal",
        "app_123",
        "Internal Testers",
        is_internal=True,
        feedback_enabled=True,
    )
    state.add_beta_group(
        "group_external",
        "app_123",
        "External Testers",
        is_internal=False,
        public_link_enabled=True,
        public_link_limit=100,
    )

    # Add beta testers
    state.add_beta_tester(
        "tester_1",
        "alice@example.com",
        first_name="Alice",
        last_name="Smith",
    )
    state.add_beta_tester(
        "tester_2",
        "bob@example.com",
        first_name="Bob",
        last_name="Jones",
    )

    # Add testers to groups
    state.add_beta_tester_to_group("tester_1", "group_internal")
    state.add_beta_tester_to_group("tester_2", "group_external")

    # Add build to group
    state.add_build_to_beta_group("build_3", "group_external")

    # Add beta build localization (What's New)
    state.add_beta_build_localization(
        "loc_1",
        "build_3",
        "en-US",
        "Bug fixes and performance improvements",
    )

    with asc_simulator.mock_context():
        yield asc_simulator


@pytest.fixture
def mock_asc_whisper_testflight(asc_simulator: ASCSimulator):
    """Simulator configured like the Whisper app with TestFlight data.

    Creates live.yooz.whisper app with builds and beta groups.

    Yields:
        ASCSimulator instance with Whisper TestFlight data
    """
    state = asc_simulator.state

    # Add Whisper app
    state.add_app(
        "whisper_app",
        "live.yooz.whisper",
        "Yooz Whisper",
        "yooz_whisper",
    )

    # Add builds
    state.add_build(
        "whisper_build_12",
        "whisper_app",
        version="0.2.6",
        build_number="12",
        processing_state="VALID",
        uploaded_date="2026-01-04T10:00:00.000Z",
    )
    state.add_build(
        "whisper_build_13",
        "whisper_app",
        version="0.2.7",
        build_number="13",
        processing_state="VALID",
        uploaded_date="2026-01-05T12:00:00.000Z",
    )

    # Add beta group
    state.add_beta_group(
        "whisper_beta",
        "whisper_app",
        "Beta Testers",
        is_internal=False,
        public_link_enabled=True,
    )

    with asc_simulator.mock_context():
        yield asc_simulator
