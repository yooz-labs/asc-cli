"""Sample app fixture data."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.simulation.state import StateManager


def load_sample_app(
    state: "StateManager",
    app_id: str = "app_123",
    bundle_id: str = "com.example.test",
    app_name: str = "Test App",
    with_subscriptions: bool = True,
    subscription_period: str | None = "ONE_MONTH",
) -> dict[str, str]:
    """Load a sample app with optional subscriptions.

    Args:
        state: StateManager to populate
        app_id: App ID
        bundle_id: Bundle identifier
        app_name: App display name
        with_subscriptions: Whether to add sample subscriptions
        subscription_period: Subscription period (None = not set)

    Returns:
        Dict with created resource IDs:
        {
            "app_id": "...",
            "group_id": "...",
            "subscription_id": "...",
        }
    """
    result = {"app_id": app_id}

    # Create app
    state.add_app(app_id, bundle_id, app_name)

    if with_subscriptions:
        # Create subscription group
        group_id = f"group_{app_id}"
        state.add_subscription_group(
            group_id=group_id,
            app_id=app_id,
            reference_name="Premium",
        )
        result["group_id"] = group_id

        # Create subscription
        subscription_id = f"sub_{app_id}"
        state.add_subscription(
            subscription_id=subscription_id,
            group_id=group_id,
            product_id=f"{bundle_id}.premium.monthly",
            name="Premium Monthly",
            state="MISSING_METADATA",
            subscription_period=subscription_period,
        )
        result["subscription_id"] = subscription_id

        # Add a localization
        loc_id = f"loc_{subscription_id}_en"
        state.add_subscription_localization(
            localization_id=loc_id,
            subscription_id=subscription_id,
            locale="en-US",
            name="Premium Monthly",
            description="Access all premium features with a monthly subscription.",
        )
        result["localization_id"] = loc_id

    return result


def load_whisper_app(state: "StateManager") -> dict[str, str]:
    """Load a sample app matching the Whisper app structure.

    This creates an app similar to the real Whisper app for testing.

    Args:
        state: StateManager to populate

    Returns:
        Dict with created resource IDs
    """
    from tests.simulation.fixtures.price_points import generate_price_points_for_subscription
    from tests.simulation.fixtures.territories import load_territories

    # Load territories first
    load_territories(state)

    # Create app (match real Whisper app attributes)
    app_id = "app_whisper"
    bundle_id = "live.yooz.whisper"
    state.add_app(
        app_id,
        bundle_id,
        "Yooz Whisper",
        sku="yooz-whisper-macos",
        content_rights_declaration="DOES_NOT_USE_THIRD_PARTY_CONTENT",
        streamlinedPurchasingEnabled=True,
    )

    # Create subscription group
    group_id = "group_whisper_premium"
    state.add_subscription_group(
        group_id=group_id,
        app_id=app_id,
        reference_name="Yooz Whisper Plans",
    )

    result = {
        "app_id": app_id,
        "group_id": group_id,
        "subscriptions": {},
    }

    # Create subscriptions (match real Whisper app)
    # Each tuple: suffix, period, price, name, group_level, family_sharable
    subscription_configs = [
        ("family.monthly", "ONE_MONTH", "6.99", "Pro Family Monthly", 1, True),
        ("family.yearly", "ONE_YEAR", "69.99", "Pro Family Yearly", 1, True),
        ("monthly", "ONE_MONTH", "2.99", "Pro Monthly", 2, False),
        ("yearly", "ONE_YEAR", "29.99", "Pro Yearly", 2, False),
    ]

    for suffix, period, _price, name, group_level, family_sharable in subscription_configs:
        # Convert suffix to use in ID (replace dots with underscores for ID)
        id_suffix = suffix.replace(".", "_")
        sub_id = f"sub_whisper_{id_suffix}"
        # Use dots in product ID (matches real API)
        product_id = f"{bundle_id}.pro.{suffix}"

        state.add_subscription(
            subscription_id=sub_id,
            group_id=group_id,
            product_id=product_id,
            name=name,
            state="MISSING_METADATA",
            subscription_period=period,
            group_level=group_level,
            family_sharable=family_sharable,
        )

        # Add localization
        loc_id = f"loc_{sub_id}_en"
        state.add_subscription_localization(
            localization_id=loc_id,
            subscription_id=sub_id,
            locale="en-US",
            name=name,
            description=f"Access Whisper Pro with {name.lower()}.",
        )

        # Generate price points
        generate_price_points_for_subscription(state, sub_id)

        result["subscriptions"][id_suffix] = sub_id

    return result
