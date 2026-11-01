"""A bounded agent composition: policy proposes, contracts and DNs dispose."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from .contracts import ContractViolation
from .dns import CommerceKernel
from .llm import LLMError

AGENT_SYSTEM_PROMPT = """You are the policy inside a bounded commerce agent.
You are not the whole agent and you have no direct application, URL, shell, or database access.
Select exactly one registered DN activation or finish after a terminal order decision.
Every DN has exactly one designated input Signal and one designated output Signal.
Y means resolved, N means definite conflict, U means unresolved or unobserved.
Never treat U as success. Never invent order or reservation identifiers.
Use this JSON form: {"dn":"DN_OrdersDraft","arguments":{"customer_id":"CUST-001","sku":"SKU-LAMP-001","quantity":1}}
DN_OrdersSubmit accepts only order_id. DN_InventoryReserve and DN_OrdersDecide accept no arguments;
their Pulse values come from the preceding output Signals. To finish: {"finish":true,"reason":"terminal status"}.
Return only one JSON object."""

ALLOWED_ARGUMENTS = {
    "DN_OrdersDraft": {"customer_id", "sku", "quantity"},
    "DN_OrdersSubmit": {"order_id"},
    "DN_InventoryReserve": set(),
    "DN_OrdersDecide": set(),
}
TERMINAL_STATUSES = {"CONFIRMED", "REJECTED", "PENDING_REVIEW"}


class Policy(Protocol):
    name: str

    def next_action(self, goal: dict[str, Any], context: dict[str, Any], history: list[dict[str, Any]], contracts: dict[str, Any]) -> dict[str, Any]: ...


class ScriptedPolicy:
    """Deterministic engine validation; its results do not evaluate LLM behavior."""

    name = "scripted"

    def next_action(self, goal: dict[str, Any], context: dict[str, Any], history: list[dict[str, Any]], contracts: dict[str, Any]) -> dict[str, Any]:
        activated = {item["dn"] for item in history if item.get("status") == "EMITTED"}
        if "DN_OrdersDraft" not in activated:
            return {"dn": "DN_OrdersDraft", "arguments": goal}
        if context.get("last_resolution") == "N" and not context.get("order_id"):
            return {"finish": True, "reason": "draft rejected"}
        if "DN_OrdersSubmit" not in activated:
            return {"dn": "DN_OrdersSubmit", "arguments": {"order_id": context["order_id"]}}
        if "DN_InventoryReserve" not in activated:
            return {"dn": "DN_InventoryReserve", "arguments": {}}
        if "DN_OrdersDecide" not in activated:
            return {"dn": "DN_OrdersDecide", "arguments": {}}
        return {"finish": True, "reason": f"terminal status {context.get('order_status')}"}


class LLMPolicy:
    def __init__(self, client: Any):
        self.client = client
        self.name = client.name

    def next_action(self, goal: dict[str, Any], context: dict[str, Any], history: list[dict[str, Any]], contracts: dict[str, Any]) -> dict[str, Any]:
        user = json.dumps({
            "goal": goal,
            "current_pulse_values": context,
            "activation_and_rejection_history": history[-8:],
            "registered_dn_contracts": contracts,
        }, ensure_ascii=False)
        return self.client.complete_json(AGENT_SYSTEM_PROMPT, user)


@dataclass(slots=True)
class AgentResult:
    outcome: str
    context: dict[str, Any]
    provenance_path: str
    summary_path: str


class CommerceAgent:
    def __init__(self, kernel: CommerceKernel, policy: Policy, max_steps: int = 8):
        self.kernel = kernel
        self.policy = policy
        self.max_steps = max_steps

    def run(self, goal: dict[str, Any]) -> AgentResult:
        context: dict[str, Any] = {}
        history: list[dict[str, Any]] = []
        recorder = self.kernel.recorder
        outcome = "max_steps_reached"
        try:
            for _ in range(self.max_steps):
                try:
                    action = self.policy.next_action(
                        goal, context, history, self.kernel.registry.public_contracts()
                    )
                except LLMError as exc:
                    outcome = "llm_error"
                    recorder.note("agent_stopped", {"reason": str(exc)})
                    break
                if action.get("finish"):
                    status = context.get("order_status")
                    if status in TERMINAL_STATUSES or (not context.get("order_id") and context.get("last_resolution") == "N"):
                        outcome = self.outcome_for(context)
                        recorder.note("agent_finished", {"reason": str(action.get("reason", "")), "outcome": outcome})
                        break
                    rejection = "Finish rejected: no terminal order decision exists"
                    history.append({"status": "AGENT_REJECTED", "error": rejection})
                    recorder.note("agent_action_rejected", {"error": rejection, "action": action})
                    continue

                dn_id = action.get("dn")
                arguments = action.get("arguments", {})
                if dn_id not in self.kernel.dns or not isinstance(arguments, dict):
                    self.reject(history, action, "Unknown DN or non-object arguments")
                    continue
                extra = sorted(set(arguments) - ALLOWED_ARGUMENTS[dn_id])
                if extra:
                    self.reject(history, action, f"Undeclared agent arguments: {extra}")
                    continue
                candidate = {**context, **arguments}
                try:
                    output = self.kernel.activate(dn_id, candidate)
                except (ContractViolation, KeyError) as exc:
                    self.reject(history, action, f"Contract rejected activation: {exc}")
                    continue
                values = output.values()
                context.update(values)
                context["last_resolution"] = output.resolution
                resolutions = context.setdefault("_signal_resolutions", {})
                resolutions[output.name] = output.resolution
                history.append({
                    "dn": dn_id,
                    "status": "EMITTED",
                    "output_signal": output.name,
                    "resolution": output.resolution,
                    "values": values,
                })
            else:
                recorder.note("agent_stopped", {"reason": "max steps reached"})
        finally:
            details = {
                "order_id": context.get("order_id"),
                "order_status": context.get("order_status"),
                "last_resolution": context.get("last_resolution"),
            }
            recorder.finish(outcome, details)
        return AgentResult(outcome, context, str(recorder.path), str(recorder.summary_path))

    @staticmethod
    def outcome_for(context: dict[str, Any]) -> str:
        if not context.get("order_id") and context.get("last_resolution") == "N":
            return "draft_rejected"
        return {
            "CONFIRMED": "confirmed",
            "REJECTED": "rejected",
            "PENDING_REVIEW": "pending_review",
        }.get(context.get("order_status"), "stopped")

    def reject(self, history: list[dict[str, Any]], action: dict[str, Any], error: str) -> None:
        history.append({"status": "AGENT_REJECTED", "action": action, "error": error})
        self.kernel.recorder.note("agent_action_rejected", {"action": action, "error": error})
