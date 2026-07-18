# type: ignore
"""Loads the solved dp table and answers state -> {action: hp-loss distribution} queries."""

from __future__ import annotations

import gzip
import pickle
from fractions import Fraction

# Restricted eval namespaces mirroring dp_solver.load_dp_table.
_KEY_GLOBALS = {"__builtins__": {}}
_VAL_GLOBALS = {"__builtins__": {}, "Fraction": Fraction}


class DpTable:
    """In-memory index of the dp data, keyed by the state vector (action stripped off)."""

    def __init__(self, by_state: dict[tuple, dict[tuple[int, ...], dict[int, Fraction]]]):
        self._by_state = by_state

    @property
    def state_count(self) -> int:
        return len(self._by_state)

    @classmethod
    def load(cls, fname: str) -> "DpTable":
        by_state: dict[tuple[int, ...], dict[tuple[int, ...], dict[int, Fraction]]] = {}
        with gzip.open(fname, mode="rb", compresslevel=6) as f:
            new_table = pickle.load(f)
        for (state, action), distribution in new_table.items():
            by_state.setdefault(state, {})[action] = distribution
        return cls(by_state)

    def actions_for(self, state: tuple) -> dict[tuple[int, ...], dict[int, Fraction]]:
        """All stored actions for a state, mapped to their hp-loss distribution. Empty if unknown."""
        return self._by_state.get(state, {})
