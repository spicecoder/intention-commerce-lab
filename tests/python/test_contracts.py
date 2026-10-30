import unittest
from pathlib import Path

from intention_commerce.contracts import ContractRegistry, ContractViolation
from intention_commerce.models import Pulse, Signal

ROOT = Path(__file__).resolve().parents[2]


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ContractRegistry(ROOT / "contracts/spaces/IS_CommerceReference.json")

    def test_pulse_requires_trivalence(self):
        with self.assertRaises(ValueError):
            Pulse("quantity", "YES", 1)

    def test_signal_rejects_duplicate_pulse_names(self):
        with self.assertRaises(ValueError):
            Signal("I_Test", (Pulse("sku", "Y", "A"), Pulse("sku", "Y", "B")))

    def test_input_signal_contains_exactly_declared_pulses(self):
        signal = self.registry.input_signal("DN_OrdersDraft", {
            "customer_id": "CUST-001", "sku": "SKU-LAMP-001", "quantity": 1,
        })
        self.registry.validate("DN_OrdersDraft", "input", signal)
        self.assertEqual(set(signal.pulse_map), {"customer_id", "sku", "quantity"})

    def test_undeclared_pulse_is_rejected(self):
        signal = Signal.from_values(
            "S_CreateDraft", "I_OrderDraftRequested",
            {"customer_id": "CUST-001", "sku": "SKU-LAMP-001", "quantity": 1, "database_url": "forbidden"},
        )
        with self.assertRaisesRegex(ContractViolation, "undeclared Pulses"):
            self.registry.validate("DN_OrdersDraft", "input", signal)

    def test_wrong_intention_is_rejected(self):
        signal = Signal.from_values(
            "S_CreateDraft", "I_SomethingElse",
            {"customer_id": "CUST-001", "sku": "SKU-LAMP-001", "quantity": 1},
        )
        with self.assertRaisesRegex(ContractViolation, "expected intention"):
            self.registry.validate("DN_OrdersDraft", "input", signal)

    def test_output_requires_returning_resolution_pulse(self):
        signal = Signal.from_values("S_ReservationRequested", "I_StockReservationRequested", {
            "order_id": "ORD-1", "customer_id": "CUST-001", "sku": "SKU-LAMP-001",
            "quantity": 1, "unit_price_cents": 12900, "total_cents": 12900,
            "currency": "USD", "shipping_address": "Address",
        })
        with self.assertRaisesRegex(ContractViolation, "resolution Pulse"):
            self.registry.validate("DN_OrdersSubmit", "output", signal)


if __name__ == "__main__":
    unittest.main()
