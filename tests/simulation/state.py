"""State management for API simulation.

Maintains in-memory state that persists across requests within a test
but resets between tests.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StateManager:
    """In-memory state for simulated API."""

    # Core entities keyed by ID
    apps: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_groups: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscriptions: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_prices: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_price_points: dict[str, dict[str, Any]] = field(default_factory=dict)
    introductory_offers: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_availabilities: dict[str, dict[str, Any]] = field(default_factory=dict)
    subscription_localizations: dict[str, dict[str, Any]] = field(default_factory=dict)
    territories: dict[str, dict[str, Any]] = field(default_factory=dict)

    # TestFlight entities
    builds: dict[str, dict[str, Any]] = field(default_factory=dict)
    beta_groups: dict[str, dict[str, Any]] = field(default_factory=dict)
    beta_testers: dict[str, dict[str, Any]] = field(default_factory=dict)
    beta_build_localizations: dict[str, dict[str, Any]] = field(default_factory=dict)
    app_encryption_declarations: dict[str, dict[str, Any]] = field(default_factory=dict)
    beta_app_review_submissions: dict[str, dict[str, Any]] = field(default_factory=dict)
    build_beta_details: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Relationships (parent_id -> child_ids)
    app_subscription_groups: dict[str, list[str]] = field(default_factory=dict)
    group_subscriptions: dict[str, list[str]] = field(default_factory=dict)
    subscription_prices_map: dict[str, list[str]] = field(default_factory=dict)
    subscription_offers_map: dict[str, list[str]] = field(default_factory=dict)
    subscription_localizations_map: dict[str, list[str]] = field(default_factory=dict)
    subscription_availability_territories: dict[str, list[str]] = field(default_factory=dict)

    # TestFlight relationships
    app_builds: dict[str, list[str]] = field(default_factory=dict)
    app_beta_groups: dict[str, list[str]] = field(default_factory=dict)
    beta_group_builds: dict[str, list[str]] = field(default_factory=dict)
    beta_group_testers: dict[str, list[str]] = field(default_factory=dict)
    build_localizations_map: dict[str, list[str]] = field(default_factory=dict)
    tester_groups: dict[str, list[str]] = field(default_factory=dict)

    # Counters for ID generation
    _id_counter: int = 1000

    def next_id(self, prefix: str = "") -> str:
        """Generate next unique ID."""
        self._id_counter += 1
        return f"{prefix}{self._id_counter}"

    def reset(self) -> None:
        """Reset all state to empty."""
        self.apps.clear()
        self.subscription_groups.clear()
        self.subscriptions.clear()
        self.subscription_prices.clear()
        self.subscription_price_points.clear()
        self.introductory_offers.clear()
        self.subscription_availabilities.clear()
        self.subscription_localizations.clear()
        self.territories.clear()

        # TestFlight entities
        self.builds.clear()
        self.beta_groups.clear()
        self.beta_testers.clear()
        self.beta_build_localizations.clear()
        self.app_encryption_declarations.clear()
        self.beta_app_review_submissions.clear()
        self.build_beta_details.clear()

        self.app_subscription_groups.clear()
        self.group_subscriptions.clear()
        self.subscription_prices_map.clear()
        self.subscription_offers_map.clear()
        self.subscription_localizations_map.clear()
        self.subscription_availability_territories.clear()

        # TestFlight relationships
        self.app_builds.clear()
        self.app_beta_groups.clear()
        self.beta_group_builds.clear()
        self.beta_group_testers.clear()
        self.build_localizations_map.clear()
        self.tester_groups.clear()

        self._id_counter = 1000

    def add_app(
        self,
        app_id: str,
        bundle_id: str,
        name: str,
        sku: str | None = None,
        primary_locale: str = "en-US",
        content_rights_declaration: str = "USES_THIRD_PARTY_CONTENT",
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add an app to state with all required attributes."""
        app = {
            "id": app_id,
            "type": "apps",
            "attributes": {
                "bundleId": bundle_id,
                "name": name,
                "sku": sku or app_id,
                "primaryLocale": primary_locale,
                "contentRightsDeclaration": content_rights_declaration,
                # Subscription webhook URLs
                "subscriptionStatusUrl": None,
                "subscriptionStatusUrlForSandbox": None,
                "subscriptionStatusUrlVersion": None,
                "subscriptionStatusUrlVersionForSandbox": None,
                # Additional app settings
                "isOrEverWasMadeForKids": False,
                "streamlinedPurchasingEnabled": False,
                "accessibilityUrl": None,
                **extra_attrs,
            },
        }
        self.apps[app_id] = app
        return app

    def add_subscription_group(
        self,
        group_id: str,
        app_id: str,
        reference_name: str,
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add a subscription group to state."""
        group = {
            "id": group_id,
            "type": "subscriptionGroups",
            "attributes": {
                "referenceName": reference_name,
                **extra_attrs,
            },
        }
        self.subscription_groups[group_id] = group
        self.app_subscription_groups.setdefault(app_id, []).append(group_id)
        return group

    def add_subscription(
        self,
        subscription_id: str,
        group_id: str,
        product_id: str,
        name: str,
        state: str = "MISSING_METADATA",
        subscription_period: str | None = None,
        family_sharable: bool = True,
        group_level: int = 1,
        review_note: str | None = None,
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add a subscription to state with all required attributes."""
        subscription = {
            "id": subscription_id,
            "type": "subscriptions",
            "attributes": {
                "productId": product_id,
                "name": name,
                "state": state,
                "subscriptionPeriod": subscription_period,
                "familySharable": family_sharable,
                "groupLevel": group_level,
                "reviewNote": review_note,
                **extra_attrs,
            },
        }
        self.subscriptions[subscription_id] = subscription
        self.group_subscriptions.setdefault(group_id, []).append(subscription_id)
        return subscription

    def add_subscription_localization(
        self,
        localization_id: str,
        subscription_id: str,
        locale: str,
        name: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Add a subscription localization to state."""
        localization = {
            "id": localization_id,
            "type": "subscriptionLocalizations",
            "attributes": {
                "locale": locale,
                "name": name,
                "description": description,
            },
        }
        self.subscription_localizations[localization_id] = localization
        self.subscription_localizations_map.setdefault(subscription_id, []).append(localization_id)
        return localization

    def add_price_point(
        self,
        price_point_id: str,
        subscription_id: str,
        territory_id: str,
        customer_price: str,
        proceeds: str,
    ) -> dict[str, Any]:
        """Add a subscription price point to state."""
        price_point = {
            "id": price_point_id,
            "type": "subscriptionPricePoints",
            "attributes": {
                "customerPrice": customer_price,
                "proceeds": proceeds,
            },
            "relationships": {
                "territory": {
                    "data": {"type": "territories", "id": territory_id},
                },
            },
        }
        self.subscription_price_points[price_point_id] = price_point
        return price_point

    def add_subscription_price(
        self,
        price_id: str,
        subscription_id: str,
        price_point_id: str,
        start_date: str | None = None,
        preserved: bool = False,
    ) -> dict[str, Any]:
        """Add a subscription price to state."""
        price = {
            "id": price_id,
            "type": "subscriptionPrices",
            "attributes": {
                "startDate": start_date,
                "preserved": preserved,
            },
            "relationships": {
                "subscription": {
                    "data": {"type": "subscriptions", "id": subscription_id},
                },
                "subscriptionPricePoint": {
                    "data": {"type": "subscriptionPricePoints", "id": price_point_id},
                },
            },
        }
        self.subscription_prices[price_id] = price
        self.subscription_prices_map.setdefault(subscription_id, []).append(price_id)
        return price

    def add_introductory_offer(
        self,
        offer_id: str,
        subscription_id: str,
        territory_id: str,
        offer_mode: str,
        duration: str,
        number_of_periods: int = 1,
        price_point_id: str | None = None,
    ) -> dict[str, Any]:
        """Add an introductory offer to state."""
        relationships: dict[str, Any] = {
            "subscription": {
                "data": {"type": "subscriptions", "id": subscription_id},
            },
            "territory": {
                "data": {"type": "territories", "id": territory_id},
            },
        }
        if price_point_id:
            relationships["subscriptionPricePoint"] = {
                "data": {"type": "subscriptionPricePoints", "id": price_point_id},
            }
        offer: dict[str, Any] = {
            "id": offer_id,
            "type": "subscriptionIntroductoryOffers",
            "attributes": {
                "offerMode": offer_mode,
                "duration": duration,
                "numberOfPeriods": number_of_periods,
            },
            "relationships": relationships,
        }
        self.introductory_offers[offer_id] = offer
        self.subscription_offers_map.setdefault(subscription_id, []).append(offer_id)
        return offer

    def set_subscription_availability(
        self,
        subscription_id: str,
        territory_ids: list[str],
        available_in_new_territories: bool = True,
    ) -> dict[str, Any]:
        """Set subscription availability for territories."""
        availability_id = f"avail_{subscription_id}"
        availability = {
            "id": availability_id,
            "type": "subscriptionAvailabilities",
            "attributes": {
                "availableInNewTerritories": available_in_new_territories,
            },
            "relationships": {
                "subscription": {
                    "data": {"type": "subscriptions", "id": subscription_id},
                },
                "availableTerritories": {
                    "data": [{"type": "territories", "id": tid} for tid in territory_ids],
                },
            },
        }
        self.subscription_availabilities[availability_id] = availability
        self.subscription_availability_territories[subscription_id] = territory_ids
        return availability

    def get_subscription_availability_territories(self, subscription_id: str) -> list[str]:
        """Get territories where subscription is available."""
        return self.subscription_availability_territories.get(subscription_id, [])

    def delete_introductory_offer(self, offer_id: str) -> bool:
        """Delete an introductory offer."""
        if offer_id not in self.introductory_offers:
            return False

        offer = self.introductory_offers.pop(offer_id)
        subscription_id = offer["relationships"]["subscription"]["data"]["id"]

        if subscription_id in self.subscription_offers_map:
            offers = self.subscription_offers_map[subscription_id]
            if offer_id in offers:
                offers.remove(offer_id)

        return True

    # =========================================================================
    # TestFlight Methods
    # =========================================================================

    def add_build(
        self,
        build_id: str,
        app_id: str,
        version: str,
        build_number: str,
        processing_state: str = "VALID",
        uploaded_date: str = "2026-01-05T10:00:00.000Z",
        min_os_version: str = "26.0",
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add a build to state."""
        build = {
            "id": build_id,
            "type": "builds",
            "attributes": {
                "version": version,
                "minOsVersion": min_os_version,
                "processingState": processing_state,
                "uploadedDate": uploaded_date,
                "expired": False,
                "usesNonExemptEncryption": None,
                "buildAudienceType": "INTERNAL_ONLY",
                **extra_attrs,
            },
            "relationships": {
                "app": {"data": {"type": "apps", "id": app_id}},
            },
        }
        self.builds[build_id] = build
        self.app_builds.setdefault(app_id, []).append(build_id)

        # Create build beta details
        details_id = f"details_{build_id}"
        self.build_beta_details[details_id] = {
            "id": details_id,
            "type": "buildBetaDetails",
            "attributes": {
                "autoNotifyEnabled": True,
                "internalBuildState": "PROCESSING",
                "externalBuildState": "PROCESSING",
            },
        }
        return build

    def add_beta_group(
        self,
        group_id: str,
        app_id: str,
        name: str,
        is_internal: bool = False,
        public_link_enabled: bool = False,
        public_link_limit: int | None = None,
        feedback_enabled: bool = True,
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add a beta group to state."""
        group = {
            "id": group_id,
            "type": "betaGroups",
            "attributes": {
                "name": name,
                "createdDate": "2026-01-01T00:00:00.000Z",
                "isInternalGroup": is_internal,
                "hasAccessToAllBuilds": False,
                "publicLinkEnabled": public_link_enabled,
                "publicLinkId": group_id[:8] if public_link_enabled else None,
                "publicLinkLimitEnabled": public_link_limit is not None,
                "publicLinkLimit": public_link_limit,
                "publicLink": f"https://testflight.apple.com/join/{group_id}"
                if public_link_enabled
                else None,
                "feedbackEnabled": feedback_enabled,
                "iosBuildsAvailableForAppleSiliconMac": True,
                "iosBuildsAvailableForAppleVision": False,
                **extra_attrs,
            },
            "relationships": {
                "app": {"data": {"type": "apps", "id": app_id}},
            },
        }
        self.beta_groups[group_id] = group
        self.app_beta_groups.setdefault(app_id, []).append(group_id)
        return group

    def add_beta_tester(
        self,
        tester_id: str,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        invite_type: str = "EMAIL",
        state: str = "INVITED",
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add a beta tester to state."""
        tester = {
            "id": tester_id,
            "type": "betaTesters",
            "attributes": {
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "inviteType": invite_type,
                "state": state,
                "appDevices": [],
                **extra_attrs,
            },
        }
        self.beta_testers[tester_id] = tester
        return tester

    def add_beta_build_localization(
        self,
        localization_id: str,
        build_id: str,
        locale: str,
        whats_new: str | None = None,
    ) -> dict[str, Any]:
        """Add a beta build localization (What's New) to state."""
        localization = {
            "id": localization_id,
            "type": "betaBuildLocalizations",
            "attributes": {
                "locale": locale,
                "whatsNew": whats_new,
            },
            "relationships": {
                "build": {"data": {"type": "builds", "id": build_id}},
            },
        }
        self.beta_build_localizations[localization_id] = localization
        self.build_localizations_map.setdefault(build_id, []).append(localization_id)
        return localization

    def add_app_encryption_declaration(
        self,
        declaration_id: str,
        build_id: str,
        uses_encryption: bool = False,
        is_exempt: bool = True,
        **extra_attrs: Any,
    ) -> dict[str, Any]:
        """Add an app encryption declaration to state."""
        declaration = {
            "id": declaration_id,
            "type": "appEncryptionDeclarations",
            "attributes": {
                "usesEncryption": uses_encryption,
                "isExempt": is_exempt,
                "containsProprietaryCryptography": False,
                "containsThirdPartyCryptography": False,
                "availableOnFrenchStore": True,
                "platform": "IOS",
                "appEncryptionDeclarationState": "APPROVED" if is_exempt else "IN_REVIEW",
                **extra_attrs,
            },
            "relationships": {
                "build": {"data": {"type": "builds", "id": build_id}},
            },
        }
        self.app_encryption_declarations[declaration_id] = declaration
        return declaration

    def add_beta_tester_to_group(self, tester_id: str, group_id: str) -> None:
        """Add a tester to a beta group."""
        self.beta_group_testers.setdefault(group_id, []).append(tester_id)
        self.tester_groups.setdefault(tester_id, []).append(group_id)

    def remove_beta_tester_from_group(self, tester_id: str, group_id: str) -> bool:
        """Remove a tester from a beta group."""
        if group_id in self.beta_group_testers and tester_id in self.beta_group_testers[group_id]:
            self.beta_group_testers[group_id].remove(tester_id)
        if tester_id in self.tester_groups and group_id in self.tester_groups[tester_id]:
            self.tester_groups[tester_id].remove(group_id)
        return True

    def add_build_to_beta_group(self, build_id: str, group_id: str) -> None:
        """Add a build to a beta group."""
        self.beta_group_builds.setdefault(group_id, []).append(build_id)

    def delete_beta_group(self, group_id: str) -> bool:
        """Delete a beta group."""
        if group_id not in self.beta_groups:
            return False

        group = self.beta_groups.pop(group_id)
        app_id = group["relationships"]["app"]["data"]["id"]

        if app_id in self.app_beta_groups and group_id in self.app_beta_groups[app_id]:
            self.app_beta_groups[app_id].remove(group_id)

        # Clean up related data
        self.beta_group_builds.pop(group_id, None)
        self.beta_group_testers.pop(group_id, None)

        return True

    def delete_beta_tester(self, tester_id: str) -> bool:
        """Delete a beta tester."""
        if tester_id not in self.beta_testers:
            return False

        self.beta_testers.pop(tester_id)

        # Remove from all groups
        for group_id in self.tester_groups.get(tester_id, []):
            testers = self.beta_group_testers.get(group_id, [])
            if tester_id in testers:
                testers.remove(tester_id)

        self.tester_groups.pop(tester_id, None)
        return True

    def submit_build_for_beta_review(self, build_id: str) -> dict[str, Any]:
        """Submit a build for beta review."""
        submission_id = self.next_id("submission_")
        submission = {
            "id": submission_id,
            "type": "betaAppReviewSubmissions",
            "attributes": {
                "betaReviewState": "WAITING_FOR_REVIEW",
                "submittedDate": "2026-01-05T10:00:00.000Z",
            },
            "relationships": {
                "build": {"data": {"type": "builds", "id": build_id}},
            },
        }
        self.beta_app_review_submissions[submission_id] = submission
        return submission
