# type: ignore
"""Loads the solved dp table and answers state -> {action: hp-loss distribution} queries."""

from __future__ import annotations

import csv
from fractions import Fraction

# Restricted eval namespaces mirroring dp_solver.load_dp_table.
_KEY_GLOBALS = {"__builtins__": {}}
_VAL_GLOBALS = {"__builtins__": {}, "Fraction": Fraction}


class DpTable:
    """In-memory index of the dp data, keyed by the 138-int state vector (action stripped off)."""

    def __init__(self, by_state: dict[tuple, dict[int, dict[int, Fraction]]]):
        self._by_state = by_state

    @property
    def state_count(self) -> int:
        return len(self._by_state)

    @classmethod
    def load(cls, fname: str) -> "DpTable":
        by_state: dict[tuple, dict[int, dict[int, Fraction]]] = {}
        with open(fname, "r") as file:
            for row in csv.reader(file):
                key = eval(row[0], _KEY_GLOBALS)
                distribution = eval(row[1], _VAL_GLOBALS)
                state, action = key[:-1], key[-1]
                by_state.setdefault(state, {})[action] = distribution
        return cls(by_state)

    def actions_for(self, state: tuple) -> dict[int, dict[int, Fraction]]:
        """All stored actions for a state, mapped to their hp-loss distribution. Empty if unknown."""
        return self._by_state.get(state, {})
