"""Command-line entry point for prototype and real-service agent runs."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .agent import CommerceAgent, LLMPolicy, ScriptedPolicy
from .applications import HttpInventory, HttpOrders, PrototypeInventory, PrototypeOrders
from .contracts import ContractRegistry
from .dns import CommerceKernel
from .llm import make_llm_client
from .provenance import ProvenanceRecorder

ROOT = Path(__file__).resolve().parent.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the bounded Intention Space commerce agent")
    parser.add_argument("--mode", choices=["prototype", "real"], default="prototype")
    parser.add_argument("--client", choices=["scripted", "ollama", "api"], default="scripted")
    parser.add_argument("--scenario", choices=["success", "insufficient", "timeout"], default="success")
    parser.add_argument("--situation-id", default="SIT-ORDER-001")
    parser.add_argument("--customer-id", default="CUST-001")
    parser.add_argument("--sku")
    parser.add_argument("--quantity", type=int)
    parser.add_argument("--max-steps", type=int, default=8)
    parser.add_argument("--provenance-dir", default=str(ROOT / "provenance"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = ContractRegistry(ROOT / "contracts" / "spaces" / "IS_CommerceReference.json")
    if args.mode == "prototype":
        orders = PrototypeOrders()
        inventory = PrototypeInventory()
        if args.scenario == "timeout":
            inventory.inject_failure("timeout")
    else:
        orders = HttpOrders(os.getenv("ORDERS_API_URL", "http://localhost:3001"))
        inventory = HttpInventory(os.getenv("INVENTORY_API_URL", "http://localhost:8081"))

    sku = args.sku or ("SKU-RARE-001" if args.scenario == "insufficient" else "SKU-LAMP-001")
    quantity = args.quantity if args.quantity is not None else 1
    goal = {"customer_id": args.customer_id, "sku": sku, "quantity": quantity}
    policy = ScriptedPolicy() if args.client == "scripted" else LLMPolicy(make_llm_client(args.client))
    recorder = ProvenanceRecorder(args.provenance_dir, args.situation_id, args.mode, args.client)
    kernel = CommerceKernel(registry, orders, inventory, recorder, args.situation_id)
    result = CommerceAgent(kernel, policy, max_steps=args.max_steps).run(goal)
    print(json.dumps({
        "outcome": result.outcome,
        "order_id": result.context.get("order_id"),
        "order_status": result.context.get("order_status"),
        "resolution": result.context.get("last_resolution"),
        "reservation_id": result.context.get("reservation_id"),
        "failure_reason": result.context.get("failure_reason"),
        "provenance": result.provenance_path,
        "summary": result.summary_path,
        "policy_note": "Scripted runs validate engine mechanics only; they do not evaluate LLM behavior." if args.client == "scripted" else None,
    }, indent=2, ensure_ascii=False))
    return 2 if result.outcome in {"llm_error", "max_steps_reached"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
