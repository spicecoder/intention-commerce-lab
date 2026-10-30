"""Prototype and HTTP adapters for the fallible enterprise applications.

Adapters expose observations to DNs. They never expose a database or generic URL
client to the agent.
"""
from __future__ import annotations

import json
import uuid
from typing import Any
from urllib import error, request

from .models import AdapterResult


class PrototypeOrders:
    def __init__(self) -> None:
        self.orders: dict[str, dict[str, Any]] = {}
        self.idempotency: dict[str, str] = {}
        self.catalog = {
            "SKU-LAMP-001": {"unitPriceCents": 12900, "currency": "USD"},
            "SKU-RARE-001": {"unitPriceCents": 49900, "currency": "USD"},
        }
        self.customers = {"CUST-001": {"shippingAddress": "21 Example Street, Kolkata 700001"}}

    def create_draft(self, customer_id: str, sku: str, quantity: int, idempotency_key: str) -> AdapterResult:
        if idempotency_key in self.idempotency:
            return AdapterResult("Y", self.orders[self.idempotency[idempotency_key]])
        if customer_id not in self.customers:
            return AdapterResult("N", error="UNKNOWN_CUSTOMER")
        if sku not in self.catalog:
            return AdapterResult("N", error="UNKNOWN_SKU")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            return AdapterResult("N", error="INVALID_QUANTITY")
        product = self.catalog[sku]
        order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"
        order = {
            "orderId": order_id,
            "customerId": customer_id,
            "sku": sku,
            "quantity": quantity,
            "unitPriceCents": product["unitPriceCents"],
            "totalCents": product["unitPriceCents"] * quantity,
            "currency": product["currency"],
            "shippingAddress": self.customers[customer_id]["shippingAddress"],
            "status": "DRAFT",
        }
        self.orders[order_id] = order
        self.idempotency[idempotency_key] = order_id
        return AdapterResult("Y", order)

    def submit_order(self, order_id: str, idempotency_key: str) -> AdapterResult:
        order = self.orders.get(order_id)
        if not order:
            return AdapterResult("N", error="ORDER_NOT_FOUND")
        if order["status"] == "DRAFT":
            order["status"] = "SUBMITTED"
        elif order["status"] not in {"SUBMITTED", "CONFIRMED", "PENDING_REVIEW"}:
            return AdapterResult("N", error="INVALID_ORDER_TRANSITION")
        return AdapterResult("Y", order)

    def decide_order(
        self, order_id: str, resolution: str, reservation_id: str, failure_reason: str
    ) -> AdapterResult:
        order = self.orders.get(order_id)
        if not order:
            return AdapterResult("N", error="ORDER_NOT_FOUND")
        if order["status"] not in {"SUBMITTED", "PENDING_REVIEW", "CONFIRMED", "REJECTED"}:
            return AdapterResult("N", error="INVALID_ORDER_TRANSITION")
        if resolution == "Y":
            if not reservation_id:
                return AdapterResult("N", error="RESERVATION_ID_REQUIRED")
            order["status"] = "CONFIRMED"
        elif resolution == "N":
            order["status"] = "REJECTED"
        else:
            order["status"] = "PENDING_REVIEW"
        order["reservationId"] = reservation_id
        order["failureReason"] = failure_reason
        return AdapterResult(resolution, order)


class PrototypeInventory:
    def __init__(self, stock: dict[str, int] | None = None):
        self.stock = dict(stock or {"SKU-LAMP-001": 5, "SKU-RARE-001": 0})
        self.reservations: dict[str, dict[str, Any]] = {}
        self.by_order: dict[str, str] = {}
        self.fail_next: str | None = None

    def inject_failure(self, failure: str) -> None:
        if failure not in {"timeout", "unavailable"}:
            raise ValueError("Supported prototype failures: timeout, unavailable")
        self.fail_next = failure

    def reserve(self, order_id: str, sku: str, quantity: int, idempotency_key: str) -> AdapterResult:
        if self.fail_next:
            failure, self.fail_next = self.fail_next, None
            return AdapterResult("U", error=f"INJECTED_{failure.upper()}")
        if order_id in self.by_order:
            return AdapterResult("Y", self.reservations[self.by_order[order_id]])
        available = self.stock.get(sku, 0)
        if available < quantity:
            return AdapterResult("N", {
                "reservationId": "",
                "reservationStatus": "NOT_RESERVED",
                "failureReason": "INSUFFICIENT_STOCK",
                "availableQuantity": available,
            }, status_code=409, error="INSUFFICIENT_STOCK")
        reservation_id = f"RSV-{uuid.uuid4().hex[:10].upper()}"
        reservation = {
            "reservationId": reservation_id,
            "orderId": order_id,
            "sku": sku,
            "quantity": quantity,
            "reservationStatus": "RESERVED",
            "failureReason": "",
        }
        self.stock[sku] -= quantity
        self.reservations[reservation_id] = reservation
        self.by_order[order_id] = reservation_id
        return AdapterResult("Y", reservation, status_code=201)


def _request_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None,
    *,
    timeout: float,
    idempotency_key: str | None = None,
) -> AdapterResult:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8") or "{}")
            return AdapterResult(
                "Y", data, status_code=response.status,
                correlation_id=response.headers.get("X-Correlation-ID") or data.get("correlationId"),
            )
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw or "{}")
        except json.JSONDecodeError:
            data = {"message": raw}
        code = data.get("code") or data.get("error") or f"HTTP_{exc.code}"
        resolution = "N" if exc.code in {400, 404, 409, 422} else "U"
        return AdapterResult(
            resolution, data, status_code=exc.code, error=code,
            correlation_id=exc.headers.get("X-Correlation-ID") or data.get("correlationId"),
        )
    except (error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return AdapterResult("U", error=f"APPLICATION_UNAVAILABLE: {exc}")


class HttpOrders:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def create_draft(self, customer_id: str, sku: str, quantity: int, idempotency_key: str) -> AdapterResult:
        return _request_json("POST", f"{self.base_url}/api/orders", {
            "customerId": customer_id, "sku": sku, "quantity": quantity,
        }, timeout=self.timeout, idempotency_key=idempotency_key)

    def submit_order(self, order_id: str, idempotency_key: str) -> AdapterResult:
        return _request_json(
            "POST", f"{self.base_url}/api/orders/{order_id}/submit", {},
            timeout=self.timeout, idempotency_key=idempotency_key,
        )

    def decide_order(self, order_id: str, resolution: str, reservation_id: str, failure_reason: str) -> AdapterResult:
        result = _request_json("POST", f"{self.base_url}/api/orders/{order_id}/reservation-decision", {
            "resolution": resolution,
            "reservationId": reservation_id,
            "failureReason": failure_reason,
        }, timeout=self.timeout, idempotency_key=f"{order_id}:decision:{resolution}")
        if result.resolution != "Y":
            return result
        # HTTP success means the decision was recorded. The business Signal must
        # retain the reservation's Y/U/N resolution rather than becoming Y by transport.
        return AdapterResult(
            resolution, result.data, status_code=result.status_code,
            error=result.error, correlation_id=result.correlation_id,
        )


class HttpInventory:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def reserve(self, order_id: str, sku: str, quantity: int, idempotency_key: str) -> AdapterResult:
        return _request_json("POST", f"{self.base_url}/api/inventory/reservations", {
            "orderId": order_id, "sku": sku, "quantity": quantity,
        }, timeout=self.timeout, idempotency_key=idempotency_key)
