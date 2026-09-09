import httpx
from langchain.tools import tool

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@tool
def get_vendor_status(vendor_code: str) -> dict[str, object]:
    """Get operational status for an external logistics vendor via REST API."""
    settings = get_settings()
    normalized_code = vendor_code.strip().upper()

    url = f"{settings.external_api_base_url}/api/v1/vendors/{normalized_code}/status"

    logger.info(
        "external_api_request_started",
        service="vendor_api",
        operation="get_vendor_status",
        vendor_code=normalized_code,
    )

    try:
        response = httpx.get(url, timeout=5.0)
    except httpx.RequestError as exc:
        logger.exception(
            "external_api_request_failed",
            service="vendor_api",
            operation="get_vendor_status",
            vendor_code=normalized_code,
            error_type=type(exc).__name__,
        )

        return {
            "success": False,
            "vendor_code": normalized_code,
            "message": "External vendor API is unavailable.",
            "error_type": type(exc).__name__,
        }

    if response.status_code == 404:
        logger.warning(
            "external_api_vendor_not_found",
            service="vendor_api",
            vendor_code=normalized_code,
            status_code=response.status_code,
        )

        return {
            "success": False,
            "vendor_code": normalized_code,
            "message": "Vendor not found.",
        }

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        logger.error(
            "external_api_request_failed",
            service="vendor_api",
            operation="get_vendor_status",
            vendor_code=normalized_code,
            status_code=response.status_code,
        )

        return {
            "success": False,
            "vendor_code": normalized_code,
            "message": "External vendor API returned an error.",
            "status_code": response.status_code,
        }

    logger.info(
        "external_api_request_completed",
        service="vendor_api",
        operation="get_vendor_status",
        vendor_code=normalized_code,
        status_code=response.status_code,
    )

    return {
        "success": True,
        "vendor": response.json(),
    }
