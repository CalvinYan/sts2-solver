from dataclasses import dataclass, field
from enum import Enum

from util.core import Action
from util.effects import Vulnerable

class Targeting(Enum):
    NONE = 0
    ENEMY_SINGLE = 1
    ALLY_SINGLE = 2

@dataclass
class Card:
    """An action with an energy cost and a target type."""
    action: Action
    cost: int
    targeting: Targeting

    def playable(self, energy: int) -> bool:
        return energy >= self.cost

@dataclass
class Strike(Card):
    action: Action = field(default_factory=lambda: Action(damage=6))
    cost: int = 1
    targeting: Targeting = Targeting.ENEMY_SINGLE

@dataclass
class Defend(Card):
    action: Action = field(default_factory=lambda: Action(block=5))
    cost: int = 1
    targeting: Targeting = Targeting.NONE

@dataclass
class Bash(Card):
    action: Action = field(default_factory=lambda: Action(damage=8, debuffs=[Vulnerable(duration=2)]))
    cost: int = 2
    targeting: Targeting = Targeting.ENEMY_SINGLE

@dataclass
class AscendersBane(Card):
    action: Action = field(default_factory=lambda: Action())
    cost: int = None
    targeting: Targeting = Targeting.NONE

    def playable(self, energy: int) -> bool:
        return False