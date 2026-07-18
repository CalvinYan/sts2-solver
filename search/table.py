"""
Represents the memoization table storing expected HP losses for different game states and actions
Key: a state-action pair consisting of a Fight vector concatenated with an action vector
(action id and target, if applicable.)
Value: the probability distribution of possible HP losses resulting from that action.
"""

from __future__ import annotations

import gzip
import pickle
from fractions import Fraction
from pathlib import Path

from card import ID_TO_CARD, Targeting


class QTable:
    def __init__(self, data: dict[tuple[tuple[int, ...], tuple[int, ...]], dict[int, Fraction]] | None = None):
        self._data = data if data is not None else {}

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __contains__(self, item):
        return item in self._data

    def __eq__(self, other):
        if not isinstance(other, QTable):
            raise NotImplementedError("Operation eq not supported between QTable and", type(other))
        return self._data == other._data

    def __str__(self):
        return str(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def update(self, other):
        if not isinstance(other, QTable):
            raise NotImplementedError("Operation update not supported between QTable and", type(other))
        self._data.update(other._data)

    def actions_for(self, state: tuple[int, ...]) -> dict[tuple[int, ...], dict[int, Fraction]]:
        """All stored actions for a state, mapped to their hp-loss distribution. Empty if unknown."""
        # TODO: Find a less dumb way to do this
        valid_actions: list[tuple[int, ...]] = [(-1,)]
        for card in ID_TO_CARD.values():
            if card().targeting == Targeting.ENEMY_SINGLE:
                valid_actions.extend([(card().id, target_id) for target_id in range(10)])
            else:
                valid_actions.append((card().id,))

        return {action: self._data[(state, action)] for action in valid_actions if (state, action) in self._data}

    @classmethod
    def load(cls, fname: str) -> "QTable":
        file_path = Path(fname)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists() or file_path.stat().st_size == 0:
            cls().dump(fname)
        with gzip.open(fname, mode="rb") as f:
            table = pickle.load(f)
        return table

    def dump(self, fname: str):
        with gzip.open(fname, mode="wb", compresslevel=6) as f:
            pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)

    def append(self, fname: str):
        merged = QTable.load(fname)
        merged.update(self)
        merged.dump(fname)
