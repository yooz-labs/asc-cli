"""Price point fixture data.

Based on Apple's price tiers and equalization rates.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.simulation.state import StateManager

# Apple's price tiers in USD (subset of actual tiers)
PRICE_TIERS_USD = [
    ("0.00", "tier_free"),
    ("0.99", "tier_1"),
    ("1.99", "tier_2"),
    ("2.99", "tier_3"),
    ("3.99", "tier_4"),
    ("4.99", "tier_5"),
    ("5.99", "tier_6"),
    ("6.99", "tier_7"),
    ("7.99", "tier_8"),
    ("8.99", "tier_9"),
    ("9.99", "tier_10"),
    ("10.99", "tier_11"),
    ("11.99", "tier_12"),
    ("12.99", "tier_13"),
    ("13.99", "tier_14"),
    ("14.99", "tier_15"),
    ("19.99", "tier_20"),
    ("24.99", "tier_25"),
    ("29.99", "tier_30"),
    ("39.99", "tier_40"),
    ("49.99", "tier_50"),
    ("59.99", "tier_60"),
    ("69.99", "tier_70"),
    ("79.99", "tier_80"),
    ("89.99", "tier_90"),
    ("99.99", "tier_100"),
]

# Approximate equalization rates relative to USD
# These are simplified rates for simulation
EQUALIZATION_RATES = {
    "USA": 1.00,
    "CAN": 1.35,
    "GBR": 0.79,
    "EUR": 0.95,  # Used for EUR countries
    "AUS": 1.55,
    "JPN": 150.0,
    "CHN": 7.20,
    "KOR": 1350.0,
    "INR": 83.0,
    "BRL": 5.0,
    "MXN": 17.5,
    "CHF": 0.88,
    "SEK": 10.5,
    "NOK": 10.8,
    "DKK": 7.0,
    "PLN": 4.0,
    "HKD": 7.85,
    "SGD": 1.35,
    "NZL": 1.65,
    "ZAR": 19.0,
    "TRY": 30.0,
    "RUB": 90.0,
}

# Map territories to their currency equalization key
TERRITORY_TO_RATE_KEY = {
    "USA": "USA",
    "CAN": "CAN",
    "GBR": "GBR",
    "DEU": "EUR",
    "FRA": "EUR",
    "ITA": "EUR",
    "ESP": "EUR",
    "NLD": "EUR",
    "BEL": "EUR",
    "AUT": "EUR",
    "IRL": "EUR",
    "PRT": "EUR",
    "FIN": "EUR",
    "GRC": "EUR",
    "AUS": "AUS",
    "NZL": "NZL",
    "JPN": "JPN",
    "CHN": "CHN",
    "KOR": "KOR",
    "HKG": "HKD",
    "SGP": "SGD",
    "IND": "INR",
    "BRA": "BRL",
    "MEX": "MXN",
    "CHE": "CHF",
    "SWE": "SEK",
    "NOR": "NOK",
    "DNK": "DKK",
    "POL": "PLN",
    "ZAF": "ZAR",
    "TUR": "TRY",
    "RUS": "RUB",
}


def calculate_proceeds(customer_price: float) -> float:
    """Calculate developer proceeds (typically 70% of customer price).

    Args:
        customer_price: Customer-facing price

    Returns:
        Developer proceeds amount
    """
    return round(customer_price * 0.70, 2)


def load_price_tiers() -> list[tuple[str, str]]:
    """Get list of price tiers.

    Returns:
        List of (price, tier_id) tuples
    """
    return PRICE_TIERS_USD.copy()


def generate_price_points_for_subscription(
    state: "StateManager",
    subscription_id: str,
    territories: list[str] | None = None,
) -> None:
    """Generate price points for a subscription across territories.

    Creates price points for each territory with equalized prices.

    Args:
        state: StateManager to populate
        subscription_id: Subscription ID
        territories: Optional list of territory IDs (defaults to all)
    """
    if territories is None:
        territories = list(state.territories.keys())

    for usd_price, tier_id in PRICE_TIERS_USD:
        usd_amount = float(usd_price)

        for territory_id in territories:
            # Get equalization rate
            rate_key = TERRITORY_TO_RATE_KEY.get(territory_id, "USA")
            rate = EQUALIZATION_RATES.get(rate_key, 1.0)

            # Calculate equalized price
            local_price = round(usd_amount * rate, 2)
            proceeds = calculate_proceeds(local_price)

            # Generate price point ID
            pp_id = f"pp_{subscription_id}_{territory_id}_{tier_id}"

            state.add_price_point(
                price_point_id=pp_id,
                subscription_id=subscription_id,
                territory_id=territory_id,
                customer_price=str(local_price),
                proceeds=str(proceeds),
            )


def find_price_point_by_usd(
    state: "StateManager",
    subscription_id: str,
    usd_price: str,
    territory_id: str = "USA",
) -> str | None:
    """Find a price point ID matching the given USD price and territory.

    Args:
        state: StateManager to search
        subscription_id: Subscription ID
        usd_price: Price in USD (e.g., "2.99")
        territory_id: Territory ID (defaults to USA)

    Returns:
        Price point ID if found, None otherwise
    """
    # Find the tier for this USD price
    tier_id = None
    for price, tid in PRICE_TIERS_USD:
        if price == usd_price:
            tier_id = tid
            break

    if not tier_id:
        return None

    # Build expected price point ID
    pp_id = f"pp_{subscription_id}_{territory_id}_{tier_id}"
    if pp_id in state.subscription_price_points:
        return pp_id

    return None
