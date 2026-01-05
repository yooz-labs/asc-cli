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
