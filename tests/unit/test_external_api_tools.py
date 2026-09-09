from typing import Any

from app.tools import external_api_tools
from app.tools.external_api_tools import get_vendor_status


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        data: dict[str, Any],
    ) -> None:
        self.status_code = status_code
        self._data = data

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._data


def test_get_vendor_status_success(monkeypatch) -> None:
    def fake_get(url: str, timeout: float):
        assert "/api/v1/vendors/ACME-LOGISTICS/status" in url
        assert timeout == 5.0

        return FakeResponse(
            200,
            {
                "vendor_code": "ACME-LOGISTICS",
                "vendor_name": "Acme Logistics",
                "operational_status": "operational",
                "active_orders": 12,
                "average_delay_hours": 1.5,
            },
        )

    monkeypatch.setattr(
        external_api_tools.httpx,
        "get",
        fake_get,
    )

    result = get_vendor_status.invoke(
        {
            "vendor_code": "ACME-LOGISTICS",
        }
    )

    assert result["success"] is True
    assert result["vendor"]["vendor_code"] == "ACME-LOGISTICS"
    assert result["vendor"]["operational_status"] == "operational"
    assert result["vendor"]["active_orders"] == 12


def test_get_vendor_status_handles_missing_vendor(monkeypatch) -> None:
    def fake_get(url: str, timeout: float):
        return FakeResponse(
            404,
            {
                "detail": "Vendor not found.",
            },
        )

    monkeypatch.setattr(
        external_api_tools.httpx,
        "get",
        fake_get,
    )

    result = get_vendor_status.invoke(
        {
            "vendor_code": "DOES-NOT-EXIST",
        }
    )

    assert result["success"] is False
    assert result["vendor_code"] == "DOES-NOT-EXIST"
    assert result["message"] == "Vendor not found."
