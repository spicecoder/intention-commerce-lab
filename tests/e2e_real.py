#!/usr/bin/env python3
"""Black-box agent test against already running real Orders and Inventory apps."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]


def wait_healthy(name: str, url: str) -> None:
    for _ in range(90):
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    print(f"{name}: healthy")
                    return
        except OSError:
            pass
        time.sleep(1)
    raise RuntimeError(f"{name} did not become healthy at {url}")


def run_scenario(scenario: str, expected: str) -> None:
    situation = f"SIT-E2E-{scenario.upper()}-{uuid.uuid4().hex[:8]}"
    completed = subprocess.run(
        [
            sys.executable, "-m", "intention_commerce.cli", "--mode", "real",
            "--client", "scripted", "--scenario", scenario, "--situation-id", situation,
        ],
        cwd=ROOT,
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"Agent failed: {completed.stdout}\n{completed.stderr}")
    result = json.loads(completed.stdout)
    if result["outcome"] != expected:
        raise AssertionError(f"{scenario}: expected {expected}, received {result}")
    print(f"{scenario}: {result['outcome']} ({result['resolution']}) — {result['provenance']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unavailable", action="store_true", help="Expect U from an Inventory started with INVENTORY_FAILURE_MODE=unavailable")
    args = parser.parse_args()
    orders_url = os.getenv("ORDERS_API_URL", "http://localhost:3001").rstrip("/")
    inventory_url = os.getenv("INVENTORY_API_URL", "http://localhost:8081").rstrip("/")
    wait_healthy("Orders", f"{orders_url}/health")
    wait_healthy("Inventory liveness", f"{inventory_url}/actuator/health/liveness")
    if args.unavailable:
        run_scenario("success", "pending_review")
    else:
        run_scenario("success", "confirmed")
        run_scenario("insufficient", "rejected")
    print("Real-service end-to-end checks passed. Scripted runs validate mechanics, not LLM quality.")


if __name__ == "__main__":
    main()
