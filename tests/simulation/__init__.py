"""App Store Connect API Simulation Engine.

This module provides a documentation-based API simulator that:
- Simulates App Store Connect API behavior based on Apple's documentation
- Maintains state (created resources appear in subsequent lists)
- Validates requests against documented constraints
- Returns proper JSON:API responses and error codes

Usage:
    @pytest.fixture
    def mock_asc_api(asc_simulator):
        with asc_simulator.mock_context():
            yield asc_simulator

    async def test_list_apps(mock_asc_api):
        client = AppStoreConnectClient()
        apps = await client.list_apps()
        assert len(apps) > 0
"""

from tests.simulation.engine import ASCSimulator
from tests.simulation.state import StateManager

__all__ = ["ASCSimulator", "StateManager"]
