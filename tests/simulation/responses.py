"""JSON:API response builders for API simulation.

All responses follow the JSON:API specification used by App Store Connect API.
"""

from typing import Any


def build_resource(
    type_: str,
    id_: str,
    attributes: dict[str, Any],
    relationships: dict[str, Any] | None = None,
    links: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a JSON:API resource object.

    Args:
        type_: Resource type (e.g., "apps", "subscriptions")
        id_: Resource identifier
        attributes: Resource attributes
        relationships: Optional relationships to other resources
        links: Optional resource links

    Returns:
        JSON:API formatted resource object
    """
    resource: dict[str, Any] = {
        "type": type_,
        "id": id_,
        "attributes": attributes,
    }
    if relationships:
        resource["relationships"] = relationships
    if links:
        resource["links"] = links
    return resource


def build_response(
    data: dict[str, Any] | list[dict[str, Any]],
    included: list[dict[str, Any]] | None = None,
    links: dict[str, str] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete JSON:API response.

    Args:
        data: Single resource or list of resources
        included: Optional related resources
        links: Optional pagination/self links
        meta: Optional metadata

    Returns:
        JSON:API formatted response
    """
    response: dict[str, Any] = {"data": data}
    if included:
        response["included"] = included
    if links:
        response["links"] = links
    if meta:
        response["meta"] = meta
    return response


def build_relationship(
    type_: str,
    id_: str,
) -> dict[str, Any]:
    """Build a JSON:API relationship reference.

    Args:
        type_: Related resource type
        id_: Related resource identifier

    Returns:
        Relationship object
    """
    return {"data": {"type": type_, "id": id_}}


def build_relationship_list(
    type_: str,
    ids: list[str],
) -> dict[str, Any]:
    """Build a JSON:API relationship reference for multiple resources.

    Args:
        type_: Related resource type
        ids: List of related resource identifiers

    Returns:
        Relationship object with list of references
    """
    return {"data": [{"type": type_, "id": id_} for id_ in ids]}


def build_paginated_response(
    data: list[dict[str, Any]],
    base_url: str,
    limit: int = 200,
    offset: int = 0,
    total: int | None = None,
    included: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a paginated JSON:API response.

    Args:
        data: Full list of resources
        base_url: Base URL for pagination links
        limit: Items per page
        offset: Current offset
        total: Total number of items (defaults to len(data))
        included: Optional related resources

    Returns:
        JSON:API formatted response with pagination links
    """
    total = total if total is not None else len(data)

    # Build pagination links
    links: dict[str, str] = {
        "self": f"{base_url}?limit={limit}&offset={offset}",
    }

    if offset + limit < total:
        links["next"] = f"{base_url}?limit={limit}&offset={offset + limit}"

    if offset > 0:
        prev_offset = max(0, offset - limit)
        links["prev"] = f"{base_url}?limit={limit}&offset={prev_offset}"

    # Slice data for current page
    page_data = data[offset : offset + limit]

    return build_response(page_data, included=included, links=links)


def build_error_response(
    status: int,
    code: str,
    title: str,
    detail: str,
    source: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a JSON:API error response.

    Args:
        status: HTTP status code
        code: Error code (e.g., "NOT_FOUND", "STATE_ERROR")
        title: Short error title
        detail: Detailed error message
        source: Optional pointer to source of error

    Returns:
        JSON:API formatted error response
    """
    error: dict[str, Any] = {
        "status": str(status),
        "code": code,
        "title": title,
        "detail": detail,
    }
    if source:
        error["source"] = source
    return {"errors": [error]}


def build_not_found_error(resource_type: str, resource_id: str) -> dict[str, Any]:
    """Build a 404 not found error response.

    Args:
        resource_type: Type of resource not found
        resource_id: ID of resource not found

    Returns:
        JSON:API formatted 404 error response
    """
    return build_error_response(
        status=404,
        code="NOT_FOUND",
        title="Not Found",
        detail=f"{resource_type} with id '{resource_id}' not found",
    )


def build_validation_error(field: str, message: str) -> dict[str, Any]:
    """Build a 400 validation error response.

    Args:
        field: Field that failed validation
        message: Validation error message

    Returns:
        JSON:API formatted 400 error response
    """
    return build_error_response(
        status=400,
        code="INVALID_REQUEST",
        title="Invalid Request",
        detail=message,
        source={"pointer": f"/data/attributes/{field}"},
    )


def build_state_error(message: str) -> dict[str, Any]:
    """Build a 409 state error response.

    Args:
        message: State error message

    Returns:
        JSON:API formatted 409 error response
    """
    return build_error_response(
        status=409,
        code="STATE_ERROR",
        title="State Error",
        detail=message,
    )


def build_relationship_error(message: str) -> dict[str, Any]:
    """Build a 409 relationship error response.

    Args:
        message: Relationship error message

    Returns:
        JSON:API formatted 409 error response
    """
    return build_error_response(
        status=409,
        code="ENTITY_ERROR.RELATIONSHIP.INVALID",
        title="Invalid Relationship",
        detail=message,
    )


def build_rate_limit_error() -> dict[str, Any]:
    """Build a 429 rate limit error response.

    Returns:
        JSON:API formatted 429 error response
    """
    return build_error_response(
        status=429,
        code="RATE_LIMIT_EXCEEDED",
        title="Rate Limit Exceeded",
        detail="Too many requests. Please retry after 60 seconds.",
    )
