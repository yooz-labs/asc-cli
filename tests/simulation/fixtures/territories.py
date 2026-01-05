"""Territory fixture data.

Based on Apple's territory list for App Store Connect.
Includes major territories with their currencies.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.simulation.state import StateManager

# Major territories with their currencies
# This is a subset - Apple supports 175 territories
TERRITORIES = [
    # North America
    {"id": "USA", "attributes": {"currency": "USD"}},
    {"id": "CAN", "attributes": {"currency": "CAD"}},
    {"id": "MEX", "attributes": {"currency": "MXN"}},
    # Europe
    {"id": "GBR", "attributes": {"currency": "GBP"}},
    {"id": "DEU", "attributes": {"currency": "EUR"}},
    {"id": "FRA", "attributes": {"currency": "EUR"}},
    {"id": "ITA", "attributes": {"currency": "EUR"}},
    {"id": "ESP", "attributes": {"currency": "EUR"}},
    {"id": "NLD", "attributes": {"currency": "EUR"}},
    {"id": "BEL", "attributes": {"currency": "EUR"}},
    {"id": "AUT", "attributes": {"currency": "EUR"}},
    {"id": "IRL", "attributes": {"currency": "EUR"}},
    {"id": "PRT", "attributes": {"currency": "EUR"}},
    {"id": "FIN", "attributes": {"currency": "EUR"}},
    {"id": "GRC", "attributes": {"currency": "EUR"}},
    {"id": "CHE", "attributes": {"currency": "CHF"}},
    {"id": "SWE", "attributes": {"currency": "SEK"}},
    {"id": "NOR", "attributes": {"currency": "NOK"}},
    {"id": "DNK", "attributes": {"currency": "DKK"}},
    {"id": "POL", "attributes": {"currency": "PLN"}},
    {"id": "CZE", "attributes": {"currency": "CZK"}},
    {"id": "HUN", "attributes": {"currency": "HUF"}},
    {"id": "ROU", "attributes": {"currency": "RON"}},
    # Asia Pacific
    {"id": "JPN", "attributes": {"currency": "JPY"}},
    {"id": "CHN", "attributes": {"currency": "CNY"}},
    {"id": "KOR", "attributes": {"currency": "KRW"}},
    {"id": "TWN", "attributes": {"currency": "TWD"}},
    {"id": "HKG", "attributes": {"currency": "HKD"}},
    {"id": "SGP", "attributes": {"currency": "SGD"}},
    {"id": "MYS", "attributes": {"currency": "MYR"}},
    {"id": "THA", "attributes": {"currency": "THB"}},
    {"id": "IDN", "attributes": {"currency": "IDR"}},
    {"id": "PHL", "attributes": {"currency": "PHP"}},
    {"id": "VNM", "attributes": {"currency": "VND"}},
    {"id": "IND", "attributes": {"currency": "INR"}},
    {"id": "AUS", "attributes": {"currency": "AUD"}},
    {"id": "NZL", "attributes": {"currency": "NZD"}},
    # Middle East
    {"id": "SAU", "attributes": {"currency": "SAR"}},
    {"id": "ARE", "attributes": {"currency": "AED"}},
    {"id": "ISR", "attributes": {"currency": "ILS"}},
    {"id": "TUR", "attributes": {"currency": "TRY"}},
    # South America
    {"id": "BRA", "attributes": {"currency": "BRL"}},
    {"id": "ARG", "attributes": {"currency": "ARS"}},
    {"id": "CHL", "attributes": {"currency": "CLP"}},
    {"id": "COL", "attributes": {"currency": "COP"}},
    {"id": "PER", "attributes": {"currency": "PEN"}},
    # Africa
    {"id": "ZAF", "attributes": {"currency": "ZAR"}},
    {"id": "EGY", "attributes": {"currency": "EGP"}},
    {"id": "NGA", "attributes": {"currency": "NGN"}},
    # Russia
    {"id": "RUS", "attributes": {"currency": "RUB"}},
]


def load_territories(state: "StateManager") -> None:
    """Load all territories into state.

    Args:
        state: StateManager to populate
    """
    for territory in TERRITORIES:
        state.territories[territory["id"]] = territory


def get_territory_ids() -> list[str]:
    """Get list of all territory IDs.

    Returns:
        List of territory ID strings
    """
    return [t["id"] for t in TERRITORIES]
