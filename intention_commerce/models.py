"""Core Pulse, Signal, and adapter values.

Pulse Responses are copied at boundaries. Only DN implementations construct new
output Responses; adapters return observations, never mutated input Pulses.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

TRIVALENCES = frozenset({"Y", "U", "N"})


@dataclass(frozen=True, slots=True)
class Pulse:
    name: str
    trivalence: str
    R: Any = None

    def __post_init__(self) -> None:
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Pulse name must be a non-empty string")
        if self.trivalence not in TRIVALENCES:
            raise ValueError(f"Invalid Trivalence {self.trivalence!r}; expected Y, U, or N")
        object.__setattr__(self, "R", deepcopy(self.R))

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "Trivalence": self.trivalence, "R": deepcopy(self.R)}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Pulse":
        return cls(name=value["name"], trivalence=value["Trivalence"], R=value.get("R"))


@dataclass(frozen=True, slots=True)
class Signal:
    intention: str
    pulses: tuple[Pulse, ...]
    name: str = ""

    def __post_init__(self) -> None:
        if not self.intention:
            raise ValueError("Signal intention is required")
        names = [pulse.name for pulse in self.pulses]
        if len(names) != len(set(names)):
            raise ValueError("A Signal cannot contain duplicate Pulse names")
        object.__setattr__(self, "pulses", tuple(deepcopy(list(self.pulses))))

    @property
    def pulse_map(self) -> dict[str, Pulse]:
        return {pulse.name: pulse for pulse in self.pulses}

    @property
    def resolution(self) -> str:
        pulse = self.pulse_map.get("resolution")
        return pulse.trivalence if pulse else "U"

    def values(self) -> dict[str, Any]:
        return {pulse.name: deepcopy(pulse.R) for pulse in self.pulses if pulse.name != "resolution"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "intention": self.intention,
            "pulses": [pulse.to_dict() for pulse in self.pulses],
        }

    @classmethod
    def from_values(
        cls,
        name: str,
        intention: str,
        values: Mapping[str, Any],
        *,
        resolution: str | None = None,
        unresolved: Iterable[str] = (),
        conflicting: Iterable[str] = (),
    ) -> "Signal":
        unresolved_set = set(unresolved)
        conflicting_set = set(conflicting)
        pulses = []
        for pulse_name, value in values.items():
            trivalence = "N" if pulse_name in conflicting_set else "U" if pulse_name in unresolved_set else "Y"
            pulses.append(Pulse(pulse_name, trivalence, value))
        if resolution is not None:
            pulses.append(Pulse("resolution", resolution, resolution))
        return cls(name=name, intention=intention, pulses=tuple(pulses))


@dataclass(frozen=True, slots=True)
class AdapterResult:
    """Observed application outcome. DNs translate this into an output Signal."""

    resolution: str
    data: Mapping[str, Any] = field(default_factory=dict)
    status_code: int | None = None
    error: str | None = None
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if self.resolution not in TRIVALENCES:
            raise ValueError("AdapterResult resolution must be Y, U, or N")
        object.__setattr__(self, "data", deepcopy(dict(self.data)))
