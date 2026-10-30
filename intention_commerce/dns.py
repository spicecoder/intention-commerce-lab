"""Bounded DN computations: one designated input and output Signal per activation."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .contracts import ContractRegistry, ContractViolation
from .models import Signal
from .provenance import ProvenanceRecorder, utc_now

ORDER_FIELDS = (
    "order_id", "customer_id", "sku", "quantity", "unit_price_cents",
    "total_cents", "currency", "shipping_address",
)


def order_values(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_id": data.get("orderId", ""),
        "customer_id": data.get("customerId", ""),
        "sku": data.get("sku", ""),
        "quantity": data.get("quantity", 0),
        "unit_price_cents": data.get("unitPriceCents", 0),
        "total_cents": data.get("totalCents", 0),
        "currency": data.get("currency", ""),
        "shipping_address": data.get("shippingAddress", ""),
    }


class BaseDN:
    dn_id = ""

    def __init__(self, registry: ContractRegistry):
        self.registry = registry

    def activate(
        self,
        input_signal: Signal,
        *,
        governing_space: str,
        recorder: ProvenanceRecorder,
        situation_id: str,
    ) -> Signal:
        started_at = utc_now()
        sequence, address = recorder.next_address(self.registry, self.dn_id)
        correlation_id = None
        try:
            if governing_space != self.registry.space_id:
                raise ContractViolation(
                    f"Situated activation requires {self.registry.space_id}; received {governing_space!r}"
                )
            self.registry.validate(self.dn_id, "input", input_signal)
            output_signal, correlation_id = self.compute(input_signal, situation_id)
            self.registry.validate(self.dn_id, "output", output_signal)
        except ContractViolation as exc:
            recorder.record(
                registry=self.registry, dn_id=self.dn_id, sequence=sequence, address=address,
                input_signal=input_signal, output_signal=None, started_at=started_at,
                status="CONTRACT_REJECTED", error=str(exc), correlation_id=correlation_id,
            )
            raise
        except Exception as exc:
            recorder.record(
                registry=self.registry, dn_id=self.dn_id, sequence=sequence, address=address,
                input_signal=input_signal, output_signal=None, started_at=started_at,
                status="ERROR", error=str(exc), correlation_id=correlation_id,
            )
            raise
        recorder.record(
            registry=self.registry, dn_id=self.dn_id, sequence=sequence, address=address,
            input_signal=input_signal, output_signal=output_signal, started_at=started_at,
            status="EMITTED", correlation_id=correlation_id,
        )
        return output_signal

    def output(self, values: dict[str, Any], resolution: str, unresolved: set[str] | None = None) -> Signal:
        spec = self.registry.contract(self.dn_id)["output"]
        return Signal.from_values(
            spec["signal"], spec["intention"], deepcopy(values),
            resolution=resolution, unresolved=unresolved or set(),
        )

    def compute(self, signal: Signal, situation_id: str) -> tuple[Signal, str | None]:
        raise NotImplementedError


class OrdersDraftDN(BaseDN):
    dn_id = "DN_OrdersDraft"

    def __init__(self, registry: ContractRegistry, orders: Any):
        super().__init__(registry)
        self.orders = orders

    def compute(self, signal: Signal, situation_id: str) -> tuple[Signal, str | None]:
        value = signal.values()
        result = self.orders.create_draft(
            value["customer_id"], value["sku"], value["quantity"], f"{situation_id}:draft"
        )
        values = order_values(dict(result.data)) if result.resolution == "Y" else {
            "order_id": "", **{name: value[name] for name in ("customer_id", "sku", "quantity")},
            "unit_price_cents": 0, "total_cents": 0, "currency": "", "shipping_address": "",
        }
        unresolved = set() if result.resolution == "Y" else {"order_id", "unit_price_cents", "total_cents", "currency", "shipping_address"}
        return self.output(values, result.resolution, unresolved), result.correlation_id


class OrdersSubmitDN(BaseDN):
    dn_id = "DN_OrdersSubmit"

    def __init__(self, registry: ContractRegistry, orders: Any):
        super().__init__(registry)
        self.orders = orders

    def compute(self, signal: Signal, situation_id: str) -> tuple[Signal, str | None]:
        order_id = signal.values()["order_id"]
        result = self.orders.submit_order(order_id, f"{order_id}:submit")
        values = order_values(dict(result.data)) if result.resolution == "Y" else {
            **{name: "" for name in ORDER_FIELDS}, "order_id": order_id,
        }
        unresolved = set() if result.resolution == "Y" else set(ORDER_FIELDS) - {"order_id"}
        return self.output(values, result.resolution, unresolved), result.correlation_id


class InventoryReserveDN(BaseDN):
    dn_id = "DN_InventoryReserve"

    def __init__(self, registry: ContractRegistry, inventory: Any):
        super().__init__(registry)
        self.inventory = inventory

    def compute(self, signal: Signal, situation_id: str) -> tuple[Signal, str | None]:
        values = signal.values()
        result = self.inventory.reserve(
            values["order_id"], values["sku"], values["quantity"], f"{values['order_id']}:reservation"
        )
        output_values = {name: values[name] for name in ORDER_FIELDS}
        output_values.update({
            "reservation_id": result.data.get("reservationId", ""),
            "reservation_status": result.data.get("reservationStatus", "UNOBSERVED" if result.resolution == "U" else "NOT_RESERVED"),
            "failure_reason": result.error or result.data.get("failureReason", "") or "",
        })
        unresolved = set() if result.resolution == "Y" else {"reservation_id"}
        return self.output(output_values, result.resolution, unresolved), result.correlation_id


class OrdersDecideDN(BaseDN):
    dn_id = "DN_OrdersDecide"

    def __init__(self, registry: ContractRegistry, orders: Any):
        super().__init__(registry)
        self.orders = orders

    def compute(self, signal: Signal, situation_id: str) -> tuple[Signal, str | None]:
        values = signal.values()
        result = self.orders.decide_order(
            values["order_id"], signal.resolution,
            values["reservation_id"], values["failure_reason"],
        )
        output_values = {name: values[name] for name in self.registry.contract(self.dn_id)["input"]["requiredPulses"]}
        output_values["order_status"] = result.data.get(
            "status", "PENDING_REVIEW" if result.resolution == "U" else "DECISION_REJECTED"
        )
        unresolved = set() if result.resolution != "U" else {"order_status"}
        return self.output(output_values, result.resolution, unresolved), result.correlation_id


class CommerceKernel:
    """The agent's only execution interface: named DN activation through S1→DN→S2."""

    def __init__(self, registry: ContractRegistry, orders: Any, inventory: Any, recorder: ProvenanceRecorder, situation_id: str):
        self.registry = registry
        self.recorder = recorder
        self.situation_id = situation_id
        self.dns = {
            "DN_OrdersDraft": OrdersDraftDN(registry, orders),
            "DN_OrdersSubmit": OrdersSubmitDN(registry, orders),
            "DN_InventoryReserve": InventoryReserveDN(registry, inventory),
            "DN_OrdersDecide": OrdersDecideDN(registry, orders),
        }

    def activate(self, dn_id: str, context: dict[str, Any]) -> Signal:
        dn = self.dns[dn_id]  # KeyError is rejected by the agent before this call.
        input_name = self.registry.contract(dn_id)["input"]["signal"]
        resolution = context.get("_signal_resolutions", {}).get(input_name)
        input_signal = self.registry.input_signal(dn_id, context, resolution=resolution)
        return dn.activate(
            input_signal,
            governing_space=self.registry.space_id,
            recorder=self.recorder,
            situation_id=self.situation_id,
        )
