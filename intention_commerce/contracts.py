"""Loads and enforces the single governing Intention Space contracts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import Signal


class ContractViolation(ValueError):
    pass


class ContractRegistry:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.document = json.loads(self.path.read_text(encoding="utf-8"))
        self.space_id = self.document["spaceId"]
        self.universe_id = self.document["universeId"]
        self.colosseum_id = self.document["colosseumId"]
        self.dns = self.document["dns"]

    def dn_ids(self) -> tuple[str, ...]:
        return tuple(self.dns)

    def contract(self, dn_id: str) -> Mapping[str, Any]:
        try:
            return self.dns[dn_id]
        except KeyError as exc:
            raise ContractViolation(f"DN {dn_id!r} is not registered in {self.space_id}") from exc

    def validate(self, dn_id: str, endpoint: str, signal: Signal) -> None:
        if endpoint not in {"input", "output"}:
            raise ValueError("endpoint must be input or output")
        expected = self.contract(dn_id)[endpoint]
        if signal.name != expected["signal"]:
            raise ContractViolation(
                f"{dn_id} {endpoint}: expected {expected['signal']}, received {signal.name!r}"
            )
        if signal.intention != expected["intention"]:
            raise ContractViolation(
                f"{dn_id} {endpoint}: expected intention {expected['intention']}, received {signal.intention!r}"
            )
        required = set(expected["requiredPulses"])
        actual = set(signal.pulse_map) - {"resolution"}
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        if missing or extra:
            raise ContractViolation(f"{dn_id} {endpoint}: missing Pulses={missing}, undeclared Pulses={extra}")
        if endpoint == "output" and "resolution" not in signal.pulse_map:
            raise ContractViolation(f"{dn_id} output lacks its returning resolution Pulse")

    def input_signal(self, dn_id: str, values: Mapping[str, Any], resolution: str | None = None) -> Signal:
        spec = self.contract(dn_id)["input"]
        missing = [name for name in spec["requiredPulses"] if name not in values]
        if missing:
            raise ContractViolation(f"Cannot construct {spec['signal']}: missing values {missing}")
        selected = {name: values[name] for name in spec["requiredPulses"]}
        return Signal.from_values(spec["signal"], spec["intention"], selected, resolution=resolution)

    def public_contracts(self) -> dict[str, Any]:
        """The only capabilities exposed to an agent or LLM policy."""
        return {
            dn_id: {
                "input": contract["input"],
                "output": contract["output"],
            }
            for dn_id, contract in self.dns.items()
        }
