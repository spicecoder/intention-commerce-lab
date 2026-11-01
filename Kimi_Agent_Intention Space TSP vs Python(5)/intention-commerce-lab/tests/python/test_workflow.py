import json
import tempfile
import unittest
from pathlib import Path

from intention_commerce.agent import CommerceAgent, ScriptedPolicy
from intention_commerce.applications import HttpOrders, PrototypeInventory, PrototypeOrders
from intention_commerce.models import AdapterResult
from unittest.mock import patch
from intention_commerce.contracts import ContractRegistry
from intention_commerce.dns import CommerceKernel
from intention_commerce.provenance import ProvenanceRecorder

ROOT = Path(__file__).resolve().parents[2]


class SequenceThenScriptedPolicy:
    name = "test-policy"

    def __init__(self, first_action):
        self.first_action = first_action
        self.first = True
        self.scripted = ScriptedPolicy()

    def next_action(self, goal, context, history, contracts):
        if self.first:
            self.first = False
            return self.first_action
        return self.scripted.next_action(goal, context, history, contracts)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.registry = ContractRegistry(ROOT / "contracts/spaces/IS_CommerceReference.json")

    def tearDown(self):
        self.temporary.cleanup()

    def run_agent(self, scenario="success", policy=None):
        orders = PrototypeOrders()
        inventory = PrototypeInventory()
        if scenario == "timeout":
            inventory.inject_failure("timeout")
        recorder = ProvenanceRecorder(self.temporary.name, f"SIT-{scenario.upper()}", "prototype", "test")
        kernel = CommerceKernel(self.registry, orders, inventory, recorder, f"SIT-{scenario.upper()}")
        goal = {
            "customer_id": "CUST-001",
            "sku": "SKU-RARE-001" if scenario == "insufficient" else "SKU-LAMP-001",
            "quantity": 1,
        }
        result = CommerceAgent(kernel, policy or ScriptedPolicy()).run(goal)
        events = [json.loads(line) for line in Path(result.provenance_path).read_text().splitlines()]
        return result, events, orders, inventory

    def test_success_emits_four_activations_and_confirms(self):
        result, events, _, _ = self.run_agent()
        self.assertEqual(result.outcome, "confirmed")
        self.assertEqual(result.context["last_resolution"], "Y")
        activations = [event for event in events if event["event"] == "dn_activation"]
        self.assertEqual(len(activations), 4)
        self.assertEqual(len({event["address"] for event in activations}), 4)
        self.assertTrue(all(event["governing_space"] == "IS_CommerceReference" for event in activations))
        self.assertEqual(activations[-1]["output_signal"]["name"], "S_OrderDecision")

    def test_insufficient_stock_propagates_n_and_rejects_order(self):
        result, _, _, _ = self.run_agent("insufficient")
        self.assertEqual(result.outcome, "rejected")
        self.assertEqual(result.context["failure_reason"], "INSUFFICIENT_STOCK")
        self.assertEqual(result.context["last_resolution"], "N")

    def test_timeout_propagates_u_and_blocks_confirmation(self):
        result, _, _, _ = self.run_agent("timeout")
        self.assertEqual(result.outcome, "pending_review")
        self.assertEqual(result.context["order_status"], "PENDING_REVIEW")
        self.assertEqual(result.context["last_resolution"], "U")
        self.assertEqual(result.context["reservation_id"], "")

    @patch("intention_commerce.applications._request_json")
    def test_http_success_does_not_turn_business_n_into_y(self, request_json):
        request_json.return_value = AdapterResult("Y", {"status": "REJECTED"}, status_code=200)
        orders = HttpOrders("http://orders.invalid")
        result = orders.decide_order("ORD-1", "N", "", "INSUFFICIENT_STOCK")
        self.assertEqual(result.resolution, "N")

    def test_duplicate_reservation_is_idempotent(self):
        inventory = PrototypeInventory()
        first = inventory.reserve("ORD-1", "SKU-LAMP-001", 1, "ORD-1:reservation")
        second = inventory.reserve("ORD-1", "SKU-LAMP-001", 1, "ORD-1:reservation")
        self.assertEqual(first.data["reservationId"], second.data["reservationId"])
        self.assertEqual(inventory.stock["SKU-LAMP-001"], 4)

    def test_llm_cannot_add_direct_url_argument(self):
        policy = SequenceThenScriptedPolicy({
            "dn": "DN_InventoryReserve", "arguments": {"url": "http://unapproved.internal/admin"},
        })
        result, events, _, _ = self.run_agent(policy=policy)
        self.assertEqual(result.outcome, "confirmed")
        rejections = [event for event in events if event["event"] == "agent_action_rejected"]
        self.assertEqual(len(rejections), 1)
        self.assertIn("Undeclared agent arguments", rejections[0]["error"])

    def test_premature_llm_finish_is_rejected(self):
        policy = SequenceThenScriptedPolicy({"finish": True, "reason": "assume success"})
        result, events, _, _ = self.run_agent(policy=policy)
        self.assertEqual(result.outcome, "confirmed")
        self.assertTrue(any(event["event"] == "agent_action_rejected" for event in events))


if __name__ == "__main__":
    unittest.main()
