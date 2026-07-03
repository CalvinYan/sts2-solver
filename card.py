from dataclasses import dataclass
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

@dataclass
class Strike(Card):
    action = Action(damage=6)
    cost = 1
    targeting = Targeting.ENEMY_SINGLE

@dataclass
class Defend(Card):
    action = Action(block=5)
    cost = 1
    targeting = Targeting.NONE

@dataclass
class Bash(Card):
    action = Action(damage=8, debuffs=[Vulnerable(duration=2)])
    cost = 2
    targeting = Targeting.ENEMY_SINGLE
