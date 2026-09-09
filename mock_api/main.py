from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(
    title="Mock Business Partner API",
    version="1.0.0",
)


class VendorStatusResponse(BaseModel):
    """Response returned for a vendor status lookup."""

    vendor_code: str
    vendor_name: str
    operational_status: str
    active_orders: int
    average_delay_hours: float


VENDORS = {
    "ACME-LOGISTICS": {
        "vendor_name": "Acme Logistics",
        "operational_status": "operational",
        "active_orders": 12,
        "average_delay_hours": 1.5,
    },
    "NORTHSTAR-FREIGHT": {
        "vendor_name": "Northstar Freight",
        "operational_status": "delayed",
        "active_orders": 27,
        "average_delay_hours": 8.0,
    },
}


@app.get("/health")
def health() -> dict[str, str]:
    """Return mock API health status."""
    return {"status": "healthy"}


@app.get(
    "/api/v1/vendors/{vendor_code}/status",
    response_model=VendorStatusResponse,
)
def get_vendor_status(vendor_code: str) -> VendorStatusResponse:
    """Return operational information for a mock external vendor."""
    normalized_code = vendor_code.strip().upper()

    vendor = VENDORS.get(normalized_code)

    if vendor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found.",
        )

    return VendorStatusResponse(
        vendor_code=normalized_code,
        **vendor,
    )
