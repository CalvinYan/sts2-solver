from __future__ import annotations

import random

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from util.core import Action
from util.effect import Vulnerable

class Targeting(Enum):
    NONE = 0
    ENEMY_SINGLE = 1
    ALLY_SINGLE = 2

@dataclass(frozen=True, repr=False)
class Card:
    """An action with an energy cost and a target type."""
    id: int
    action: Action
    cost: int
    targeting: Targeting

    def playable(self, energy: int) -> bool:
        return energy >= self.cost

    def to_vector(self) -> np.ndarray:
        base = np.zeros(max(ID_TO_CARD.keys()) + 1, dtype=int)
        if self is not None:
            base[self.id] = 1
        return base

    def __repr__(self):
        return type(self).__name__

@dataclass(frozen=True, repr=False)
class Strike(Card):
    id: int = 0
    action: Action = field(default_factory=lambda: Action(damage=6))
    cost: int = 1
    targeting: Targeting = Targeting.ENEMY_SINGLE

@dataclass(frozen=True, repr=False)
class Defend(Card):
    id: int = 1
    action: Action = field(default_factory=lambda: Action(block=5))
    cost: int = 1
    targeting: Targeting = Targeting.NONE

@dataclass(frozen=True, repr=False)
class Bash(Card):
    id: int = 2
    action: Action = field(default_factory=lambda: Action(damage=8, debuffs=[Vulnerable(duration=2)]))
    cost: int = 2
    targeting: Targeting = Targeting.ENEMY_SINGLE

@dataclass(frozen=True, repr=False)
class AscendersBane(Card):
    id: int = 11
    action: Action = field(default_factory=lambda: Action())
    cost: int = None
    targeting: Targeting = Targeting.NONE

    def playable(self, energy: int) -> bool:
        return False

ID_TO_CARD = {
    Strike.id: Strike,
    Defend.id: Defend,
    Bash.id: Bash,
    AscendersBane.id: AscendersBane
}