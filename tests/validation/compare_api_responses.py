"""Compare real App Store Connect API responses with simulation.

This script helps validate that our simulation accurately matches Apple's API
by comparing actual API responses for the Whisper app with simulated responses.

Usage:
    python tests/validation/compare_api_responses.py

Prerequisites:
    - ASC credentials configured (ASC_ISSUER_ID, ASC_KEY_ID, ASC_PRIVATE_KEY)
    - Whisper app exists in App Store Connect
"""

import asyncio
import json
from pathlib import Path
from typing import Any

from asc_cli.api.client import AppStoreConnectClient
from tests.simulation import ASCSimulator
from tests.simulation.fixtures.apps import load_whisper_app


class ResponseComparator:
    """Compare real API responses with simulation responses."""

    def __init__(self):
        self.real_client = AppStoreConnectClient()
        self.simulator = ASCSimulator()
        load_whisper_app(self.simulator.state)
        self.discrepancies: list[dict[str, Any]] = []

    def compare_dicts(
        self,
        path: str,
        real: dict[str, Any],
        simulated: dict[str, Any],
        ignore_keys: set[str] | None = None,
    ) -> list[str]:
        """Compare two dictionaries and return differences.

        Args:
            path: JSONPath to current location
            real: Real API response
            simulated: Simulated response
            ignore_keys: Keys to ignore in comparison (e.g., timestamps, IDs)

        Returns:
            List of difference descriptions
        """
        ignore_keys = ignore_keys or {"id", "links"}
        diffs = []

        # Check for missing keys
        real_keys = set(real.keys()) - ignore_keys
        sim_keys = set(simulated.keys()) - ignore_keys

        for key in real_keys - sim_keys:
            diffs.append(f"{path}.{key}: Missing in simulation")

        for key in sim_keys - real_keys:
            diffs.append(f"{path}.{key}: Extra in simulation (not in real API)")

        # Compare common keys
        for key in real_keys & sim_keys:
            real_val = real[key]
            sim_val = simulated[key]

            if isinstance(real_val, dict) and isinstance(sim_val, dict):
                diffs.extend(self.compare_dicts(f"{path}.{key}", real_val, sim_val, ignore_keys))
            elif isinstance(real_val, list) and isinstance(sim_val, list):
                if len(real_val) != len(sim_val):
                    diffs.append(
                        f"{path}.{key}: Different lengths "
                        f"(real={len(real_val)}, sim={len(sim_val)})"
                    )
                else:
                    for i, (r, s) in enumerate(zip(real_val, sim_val, strict=False)):
                        if isinstance(r, dict) and isinstance(s, dict):
                            diffs.extend(
                                self.compare_dicts(f"{path}.{key}[{i}]", r, s, ignore_keys)
                            )
            elif real_val != sim_val:
                # For values, check type first
                if type(real_val) is not type(sim_val):
                    diffs.append(
                        f"{path}.{key}: Type mismatch (real={type(real_val).__name__}, "
                        f"sim={type(sim_val).__name__})"
                    )
                else:
                    diffs.append(
                        f"{path}.{key}: Value mismatch (real={real_val!r}, sim={sim_val!r})"
                    )

        return diffs

    async def compare_app_response(self) -> dict[str, Any]:
        """Compare app retrieval responses."""
        print("\n=== Testing: GET /apps (filter by bundle ID) ===")

        # Get real response
        real_app = await self.real_client.get_app("live.yooz.whisper")

        # Get simulated response
        with self.simulator.mock_context():
            sim_client = AppStoreConnectClient()
            sim_app = await sim_client.get_app("live.yooz.whisper")
            await sim_client.close()

        if not real_app:
            return {"endpoint": "GET /apps", "status": "SKIP", "reason": "App not found"}

        # Compare
        diffs = self.compare_dicts("app", real_app, sim_app or {})

        result = {
            "endpoint": "GET /apps?filter[bundleId]=live.yooz.whisper",
            "status": "PASS" if not diffs else "FAIL",
            "discrepancies": diffs,
        }

        if diffs:
            self.discrepancies.append(result)

        return result

    async def compare_subscription_groups(self, app_id: str) -> dict[str, Any]:
        """Compare subscription groups response."""
        print("\n=== Testing: GET /apps/{id}/subscriptionGroups ===")

        # Get real response
        real_groups = await self.real_client.list_subscription_groups(app_id)

        # Get simulated response
        with self.simulator.mock_context():
            sim_client = AppStoreConnectClient()
            sim_groups = await sim_client.list_subscription_groups("app_whisper")
            await sim_client.close()

        # Compare structure
        if len(real_groups) != len(sim_groups):
            return {
                "endpoint": f"GET /apps/{app_id}/subscriptionGroups",
                "status": "FAIL",
                "discrepancies": [
                    f"Different number of groups: real={len(real_groups)}, sim={len(sim_groups)}"
                ],
            }

        diffs = []
        for real_group, sim_group in zip(real_groups, sim_groups, strict=False):
            diffs.extend(self.compare_dicts("group", real_group, sim_group))

        result = {
            "endpoint": f"GET /apps/{app_id}/subscriptionGroups",
            "status": "PASS" if not diffs else "FAIL",
            "discrepancies": diffs,
        }

        if diffs:
            self.discrepancies.append(result)

        return result

    async def compare_subscriptions(self, group_id: str) -> dict[str, Any]:
        """Compare subscriptions list response."""
        print(f"\n=== Testing: GET /subscriptionGroups/{group_id}/subscriptions ===")

        # Get real response
        real_subs = await self.real_client.list_subscriptions(group_id)

        # Get simulated response
        with self.simulator.mock_context():
            sim_client = AppStoreConnectClient()
            sim_subs = await sim_client.list_subscriptions("group_whisper_premium")
            await sim_client.close()

        diffs = []
        for real_sub, sim_sub in zip(real_subs, sim_subs, strict=False):
            diffs.extend(self.compare_dicts("subscription", real_sub, sim_sub))

        result = {
            "endpoint": f"GET /subscriptionGroups/{group_id}/subscriptions",
            "status": "PASS" if not diffs else "FAIL",
            "discrepancies": diffs,
        }

        if diffs:
            self.discrepancies.append(result)

        return result

    async def run_comparison(self) -> dict[str, Any]:
        """Run full comparison suite."""
        print("=" * 80)
        print("App Store Connect API Validation")
        print("Comparing: Real Whisper App vs Simulation")
        print("=" * 80)

        results = []

        try:
            # 1. Compare app response
            app_result = await self.compare_app_response()
            results.append(app_result)

            if app_result["status"] == "SKIP":
                print("\n⚠️ Whisper app not found - cannot continue validation")
                return {"results": results, "summary": {"total": 1, "passed": 0, "failed": 0}}

            # Get app ID for further tests
            real_app = await self.real_client.get_app("live.yooz.whisper")
            app_id = real_app["id"] if real_app else None

            if app_id:
                # 2. Compare subscription groups
                groups_result = await self.compare_subscription_groups(app_id)
                results.append(groups_result)

                # Get first group ID
                real_groups = await self.real_client.list_subscription_groups(app_id)
                if real_groups:
                    group_id = real_groups[0]["id"]

                    # 3. Compare subscriptions
                    subs_result = await self.compare_subscriptions(group_id)
                    results.append(subs_result)

        finally:
            await self.real_client.close()

        # Summary
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")

        if self.discrepancies:
            print("\n⚠️ DISCREPANCIES FOUND:")
            for disc in self.discrepancies:
                print(f"\n{disc['endpoint']}:")
                for diff in disc["discrepancies"]:
                    print(f"  - {diff}")

        return {
            "results": results,
            "summary": {"total": len(results), "passed": passed, "failed": failed},
        }


async def main():
    """Run the validation."""
    comparator = ResponseComparator()
    results = await comparator.run_comparison()

    # Save results
    output_path = Path("tests/validation/comparison_results.json")
    with output_path.open("w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to: tests/validation/comparison_results.json")


if __name__ == "__main__":
    asyncio.run(main())
