"""Append-only situated activation provenance."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Signal


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return cleaned or "SIT-UNNAMED"


class ProvenanceRecorder:
    def __init__(self, directory: str | Path, situation_id: str, mode: str, client: str):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.situation_id = safe_id(situation_id)
        self.run_id = f"{self.situation_id}-{uuid.uuid4().hex[:12]}"
        self.path = self.directory / f"{self.run_id}.jsonl"
        self.summary_path = self.directory / f"{self.run_id}.summary.json"
        self.sequence = 0
        self.metadata = {
            "run_id": self.run_id,
            "situation_id": self.situation_id,
            "mode": mode,
            "client": client,
            "started_at": utc_now(),
        }

    def next_address(self, registry: Any, dn_id: str) -> tuple[int, str]:
        self.sequence += 1
        address = (
            f"{registry.universe_id}/{registry.colosseum_id}/{registry.space_id}/"
            f"{self.situation_id}/{dn_id}/α{self.sequence:02d}"
        )
        return self.sequence, address

    def record(
        self,
        *,
        registry: Any,
        dn_id: str,
        sequence: int,
        address: str,
        input_signal: Signal,
        output_signal: Signal | None,
        started_at: str,
        status: str,
        error: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        event = {
            "event": "dn_activation",
            "activation_id": str(uuid.uuid4()),
            "run_id": self.run_id,
            "sequence": sequence,
            "address": address,
            "governing_space": registry.space_id,
            "dn": dn_id,
            "status": status,
            "started_at": started_at,
            "ended_at": utc_now(),
            "input_signal": input_signal.to_dict(),
            "output_signal": output_signal.to_dict() if output_signal else None,
            "application_correlation_id": correlation_id,
            "error": error,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def note(self, event_type: str, details: dict[str, Any]) -> None:
        event = {
            "event": event_type,
            "run_id": self.run_id,
            "recorded_at": utc_now(),
            **details,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def finish(self, outcome: str, details: dict[str, Any] | None = None) -> None:
        summary = {
            **self.metadata,
            "finished_at": utc_now(),
            "outcome": outcome,
            "activation_count": self.sequence,
            "provenance_file": self.path.name,
            **(details or {}),
        }
        self.summary_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
