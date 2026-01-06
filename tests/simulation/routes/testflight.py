"""Route handlers for TestFlight endpoints."""

import json
from typing import TYPE_CHECKING

import httpx

from tests.simulation.responses import (
    build_not_found_error,
    build_resource,
    build_response,
)

if TYPE_CHECKING:
    from tests.simulation.state import StateManager


# =============================================================================
# Builds
# =============================================================================


def handle_list_builds(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle GET /builds with query parameters.

    Supports:
        - filter[app]: Filter by app ID (required for listing)
        - filter[version]: Filter by build version (for get_build_by_version)
        - filter[processingState]: Filter by processing state
        - limit: Max results to return
    """
    params = dict(request.url.params)

    # Get app_id from filter
    app_id = params.get("filter[app]")
    if not app_id:
        # Return empty list if no app filter
        return httpx.Response(200, json=build_response([]))

    if app_id not in state.apps:
        return httpx.Response(404, json=build_not_found_error("App", app_id))

    limit = int(params.get("limit", "10"))

    build_ids = state.app_builds.get(app_id, [])
    builds = [state.builds[bid] for bid in build_ids if bid in state.builds]

    # Apply version filter if present (for get_build_by_version)
    version_filter = params.get("filter[version]")
    if version_filter:
        # The version is actually the build number in CFBundleVersion
        builds = [b for b in builds if str(b["attributes"].get("version")) == version_filter]

    # Apply processing state filter if present
    processing_state = params.get("filter[processingState]")
    if processing_state:
        builds = [b for b in builds if b["attributes"].get("processingState") == processing_state]

    # Sort by uploaded date descending (newest first)
    builds.sort(key=lambda b: b["attributes"].get("uploadedDate", ""), reverse=True)

    # Limit results
    builds = builds[:limit]

    data = [
        build_resource("builds", b["id"], b["attributes"], b.get("relationships")) for b in builds
    ]
    return httpx.Response(200, json=build_response(data))


def handle_get_build(
    request: httpx.Request,
    state: "StateManager",
    build_id: str,
) -> httpx.Response:
    """Handle GET /builds/{id}."""
    if build_id not in state.builds:
        return httpx.Response(404, json=build_not_found_error("Build", build_id))

    build = state.builds[build_id]
    return httpx.Response(
        200,
        json=build_response(
            build_resource("builds", build_id, build["attributes"], build.get("relationships"))
        ),
    )


# =============================================================================
# Beta Build Localizations
# =============================================================================


def handle_list_beta_build_localizations(
    request: httpx.Request,
    state: "StateManager",
    build_id: str,
) -> httpx.Response:
    """Handle GET /builds/{id}/betaBuildLocalizations."""
    if build_id not in state.builds:
        return httpx.Response(404, json=build_not_found_error("Build", build_id))

    loc_ids = state.build_localizations_map.get(build_id, [])
    localizations = [
        state.beta_build_localizations[lid]
        for lid in loc_ids
        if lid in state.beta_build_localizations
    ]

    data = [
        build_resource(
            "betaBuildLocalizations", loc["id"], loc["attributes"], loc.get("relationships")
        )
        for loc in localizations
    ]
    return httpx.Response(200, json=build_response(data))


def handle_create_beta_build_localization(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle POST /betaBuildLocalizations."""
    body = json.loads(request.content)
    data = body.get("data", {})
    attrs = data.get("attributes", {})
    relationships = data.get("relationships", {})

    build_id = relationships.get("build", {}).get("data", {}).get("id")
    if not build_id or build_id not in state.builds:
        return httpx.Response(404, json=build_not_found_error("Build", build_id or "unknown"))

    locale = attrs.get("locale", "en-US")
    whats_new = attrs.get("whatsNew")

    loc_id = state.next_id("loc_")
    localization = state.add_beta_build_localization(loc_id, build_id, locale, whats_new)

    return httpx.Response(
        201,
        json=build_response(
            build_resource(
                "betaBuildLocalizations",
                loc_id,
                localization["attributes"],
                localization.get("relationships"),
            )
        ),
    )


def handle_update_beta_build_localization(
    request: httpx.Request,
    state: "StateManager",
    localization_id: str,
) -> httpx.Response:
    """Handle PATCH /betaBuildLocalizations/{id}."""
    if localization_id not in state.beta_build_localizations:
        return httpx.Response(
            404, json=build_not_found_error("BetaBuildLocalization", localization_id)
        )

    body = json.loads(request.content)
    data = body.get("data", {})
    attrs = data.get("attributes", {})

    localization = state.beta_build_localizations[localization_id]
    if "whatsNew" in attrs:
        localization["attributes"]["whatsNew"] = attrs["whatsNew"]

    return httpx.Response(
        200,
        json=build_response(
            build_resource(
                "betaBuildLocalizations",
                localization_id,
                localization["attributes"],
                localization.get("relationships"),
            )
        ),
    )


# =============================================================================
# App Encryption Declarations
# =============================================================================


def handle_get_build_encryption_declaration(
    request: httpx.Request,
    state: "StateManager",
    build_id: str,
) -> httpx.Response:
    """Handle GET /builds/{id}/appEncryptionDeclaration."""
    if build_id not in state.builds:
        return httpx.Response(404, json=build_not_found_error("Build", build_id))

    # Find declaration for this build
    for decl in state.app_encryption_declarations.values():
        if decl["relationships"]["build"]["data"]["id"] == build_id:
            return httpx.Response(
                200,
                json=build_response(
                    build_resource(
                        "appEncryptionDeclarations",
                        decl["id"],
                        decl["attributes"],
                        decl.get("relationships"),
                    )
                ),
            )

    # No declaration found - return empty
    return httpx.Response(200, json={"data": None})


def handle_create_app_encryption_declaration(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle POST /appEncryptionDeclarations."""
    body = json.loads(request.content)
    data = body.get("data", {})
    attrs = data.get("attributes", {})
    relationships = data.get("relationships", {})

    build_id = relationships.get("build", {}).get("data", {}).get("id")
    if not build_id or build_id not in state.builds:
        return httpx.Response(404, json=build_not_found_error("Build", build_id or "unknown"))

    uses_encryption = attrs.get("usesEncryption", False)
    is_exempt = attrs.get("isExempt", True)

    decl_id = state.next_id("encr_")
    declaration = state.add_app_encryption_declaration(
        decl_id, build_id, uses_encryption, is_exempt
    )

    return httpx.Response(
        201,
        json=build_response(
            build_resource(
                "appEncryptionDeclarations",
                decl_id,
                declaration["attributes"],
                declaration.get("relationships"),
            )
        ),
    )


# =============================================================================
# Beta App Review Submissions
# =============================================================================


def handle_create_beta_app_review_submission(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle POST /betaAppReviewSubmissions."""
    body = json.loads(request.content)
    data = body.get("data", {})
    relationships = data.get("relationships", {})

    build_id = relationships.get("build", {}).get("data", {}).get("id")
    if not build_id or build_id not in state.builds:
        return httpx.Response(404, json=build_not_found_error("Build", build_id or "unknown"))

    submission = state.submit_build_for_beta_review(build_id)

    return httpx.Response(
        201,
        json=build_response(
            build_resource(
                "betaAppReviewSubmissions",
                submission["id"],
                submission["attributes"],
                submission.get("relationships"),
            )
        ),
    )


# =============================================================================
# Beta Groups
# =============================================================================


def handle_list_beta_groups(
    request: httpx.Request,
    state: "StateManager",
    app_id: str,
) -> httpx.Response:
    """Handle GET /apps/{id}/betaGroups."""
    if app_id not in state.apps:
        return httpx.Response(404, json=build_not_found_error("App", app_id))

    params = dict(request.url.params)
    limit = int(params.get("limit", "50"))

    group_ids = state.app_beta_groups.get(app_id, [])
    groups = [state.beta_groups[gid] for gid in group_ids if gid in state.beta_groups]

    # Limit results
    groups = groups[:limit]

    data = [
        build_resource("betaGroups", g["id"], g["attributes"], g.get("relationships"))
        for g in groups
    ]
    return httpx.Response(200, json=build_response(data))


def handle_get_beta_group(
    request: httpx.Request,
    state: "StateManager",
    group_id: str,
) -> httpx.Response:
    """Handle GET /betaGroups/{id}."""
    if group_id not in state.beta_groups:
        return httpx.Response(404, json=build_not_found_error("BetaGroup", group_id))

    group = state.beta_groups[group_id]
    return httpx.Response(
        200,
        json=build_response(
            build_resource("betaGroups", group_id, group["attributes"], group.get("relationships"))
        ),
    )


def handle_create_beta_group(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle POST /betaGroups."""
    body = json.loads(request.content)
    data = body.get("data", {})
    attrs = data.get("attributes", {})
    relationships = data.get("relationships", {})

    app_id = relationships.get("app", {}).get("data", {}).get("id")
    if not app_id or app_id not in state.apps:
        return httpx.Response(404, json=build_not_found_error("App", app_id or "unknown"))

    name = attrs.get("name", "Untitled Group")
    is_internal = attrs.get("isInternalGroup", False)
    public_link_enabled = attrs.get("publicLinkEnabled", False)
    public_link_limit = attrs.get("publicLinkLimit")
    feedback_enabled = attrs.get("feedbackEnabled", True)

    group_id = state.next_id("group_")
    group = state.add_beta_group(
        group_id,
        app_id,
        name,
        is_internal=is_internal,
        public_link_enabled=public_link_enabled,
        public_link_limit=public_link_limit,
        feedback_enabled=feedback_enabled,
    )

    return httpx.Response(
        201,
        json=build_response(
            build_resource("betaGroups", group_id, group["attributes"], group.get("relationships"))
        ),
    )


def handle_update_beta_group(
    request: httpx.Request,
    state: "StateManager",
    group_id: str,
) -> httpx.Response:
    """Handle PATCH /betaGroups/{id}."""
    if group_id not in state.beta_groups:
        return httpx.Response(404, json=build_not_found_error("BetaGroup", group_id))

    body = json.loads(request.content)
    data = body.get("data", {})
    attrs = data.get("attributes", {})

    group = state.beta_groups[group_id]

    # Update allowed fields
    for field in ["name", "publicLinkEnabled", "publicLinkLimit", "feedbackEnabled"]:
        if field in attrs:
            group["attributes"][field] = attrs[field]

    # Update public link if enabled
    if attrs.get("publicLinkEnabled"):
        group["attributes"]["publicLink"] = f"https://testflight.apple.com/join/{group_id}"
    elif "publicLinkEnabled" in attrs and not attrs["publicLinkEnabled"]:
        group["attributes"]["publicLink"] = None

    return httpx.Response(
        200,
        json=build_response(
            build_resource("betaGroups", group_id, group["attributes"], group.get("relationships"))
        ),
    )


def handle_delete_beta_group(
    request: httpx.Request,
    state: "StateManager",
    group_id: str,
) -> httpx.Response:
    """Handle DELETE /betaGroups/{id}."""
    if not state.delete_beta_group(group_id):
        return httpx.Response(404, json=build_not_found_error("BetaGroup", group_id))

    return httpx.Response(200, json={})


def handle_add_builds_to_beta_group(
    request: httpx.Request,
    state: "StateManager",
    group_id: str,
) -> httpx.Response:
    """Handle POST /betaGroups/{id}/relationships/builds."""
    if group_id not in state.beta_groups:
        return httpx.Response(404, json=build_not_found_error("BetaGroup", group_id))

    body = json.loads(request.content)
    build_refs = body.get("data", [])

    for ref in build_refs:
        build_id = ref.get("id")
        if build_id and build_id in state.builds:
            state.add_build_to_beta_group(build_id, group_id)

    # Return 200 with empty JSON (client always parses JSON)
    return httpx.Response(200, json={})


# =============================================================================
# Beta Testers
# =============================================================================


def handle_list_beta_testers(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle GET /betaTesters."""
    params = dict(request.url.params)
    limit = int(params.get("limit", "50"))

    testers = list(state.beta_testers.values())

    # Apply filters
    email_filter = params.get("filter[email]")
    if email_filter:
        testers = [t for t in testers if t["attributes"].get("email") == email_filter]

    app_filter = params.get("filter[apps]")
    if app_filter:
        # Filter testers by app (through groups)
        app_group_ids = state.app_beta_groups.get(app_filter, [])
        tester_ids_in_app = set()
        for gid in app_group_ids:
            tester_ids_in_app.update(state.beta_group_testers.get(gid, []))
        testers = [t for t in testers if t["id"] in tester_ids_in_app]

    # Limit results
    testers = testers[:limit]

    data = [build_resource("betaTesters", t["id"], t["attributes"]) for t in testers]
    return httpx.Response(200, json=build_response(data))


def handle_get_beta_tester(
    request: httpx.Request,
    state: "StateManager",
    tester_id: str,
) -> httpx.Response:
    """Handle GET /betaTesters/{id}."""
    if tester_id not in state.beta_testers:
        return httpx.Response(404, json=build_not_found_error("BetaTester", tester_id))

    tester = state.beta_testers[tester_id]
    return httpx.Response(
        200,
        json=build_response(build_resource("betaTesters", tester_id, tester["attributes"])),
    )


def handle_create_beta_tester(
    request: httpx.Request,
    state: "StateManager",
) -> httpx.Response:
    """Handle POST /betaTesters."""
    body = json.loads(request.content)
    data = body.get("data", {})
    attrs = data.get("attributes", {})
    relationships = data.get("relationships", {})

    email = attrs.get("email")
    if not email:
        from tests.simulation.responses import build_validation_error

        return httpx.Response(400, json=build_validation_error("email", "Email is required"))

    first_name = attrs.get("firstName")
    last_name = attrs.get("lastName")

    tester_id = state.next_id("tester_")
    tester = state.add_beta_tester(tester_id, email, first_name, last_name)

    # Add to groups if specified
    group_refs = relationships.get("betaGroups", {}).get("data", [])
    for ref in group_refs:
        group_id = ref.get("id")
        if group_id and group_id in state.beta_groups:
            state.add_beta_tester_to_group(tester_id, group_id)

    return httpx.Response(
        201,
        json=build_response(build_resource("betaTesters", tester_id, tester["attributes"])),
    )


def handle_delete_beta_tester(
    request: httpx.Request,
    state: "StateManager",
    tester_id: str,
) -> httpx.Response:
    """Handle DELETE /betaTesters/{id}."""
    if not state.delete_beta_tester(tester_id):
        return httpx.Response(404, json=build_not_found_error("BetaTester", tester_id))

    return httpx.Response(200, json={})


def handle_add_beta_tester_to_groups(
    request: httpx.Request,
    state: "StateManager",
    tester_id: str,
) -> httpx.Response:
    """Handle POST /betaTesters/{id}/relationships/betaGroups."""
    if tester_id not in state.beta_testers:
        return httpx.Response(404, json=build_not_found_error("BetaTester", tester_id))

    body = json.loads(request.content)
    group_refs = body.get("data", [])

    for ref in group_refs:
        group_id = ref.get("id")
        if group_id and group_id in state.beta_groups:
            state.add_beta_tester_to_group(tester_id, group_id)

    return httpx.Response(200, json={})


def handle_remove_beta_tester_from_groups(
    request: httpx.Request,
    state: "StateManager",
    tester_id: str,
) -> httpx.Response:
    """Handle DELETE /betaTesters/{id}/relationships/betaGroups."""
    if tester_id not in state.beta_testers:
        return httpx.Response(404, json=build_not_found_error("BetaTester", tester_id))

    body = json.loads(request.content)
    group_refs = body.get("data", [])

    for ref in group_refs:
        group_id = ref.get("id")
        if group_id:
            state.remove_beta_tester_from_group(tester_id, group_id)

    return httpx.Response(200, json={})


# =============================================================================
# Build Beta Details
# =============================================================================


def handle_get_build_beta_details(
    request: httpx.Request,
    state: "StateManager",
    build_id: str,
) -> httpx.Response:
    """Handle GET /builds/{id}/buildBetaDetail."""
    if build_id not in state.builds:
        return httpx.Response(404, json=build_not_found_error("Build", build_id))

    details_id = f"details_{build_id}"
    if details_id not in state.build_beta_details:
        return httpx.Response(404, json=build_not_found_error("BuildBetaDetail", details_id))

    details = state.build_beta_details[details_id]
    return httpx.Response(
        200,
        json=build_response(build_resource("buildBetaDetails", details_id, details["attributes"])),
    )


def handle_update_build_beta_details(
    request: httpx.Request,
    state: "StateManager",
    details_id: str,
) -> httpx.Response:
    """Handle PATCH /buildBetaDetails/{id}."""
    if details_id not in state.build_beta_details:
        return httpx.Response(404, json=build_not_found_error("BuildBetaDetail", details_id))

    body = json.loads(request.content)
    data = body.get("data", {})
    attrs = data.get("attributes", {})

    details = state.build_beta_details[details_id]

    # Update allowed fields
    if "autoNotifyEnabled" in attrs:
        details["attributes"]["autoNotifyEnabled"] = attrs["autoNotifyEnabled"]

    return httpx.Response(
        200,
        json=build_response(build_resource("buildBetaDetails", details_id, details["attributes"])),
    )
