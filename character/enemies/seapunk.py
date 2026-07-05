from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Strength

@dataclass(repr=False)
class SeaKick(Intent):
    id: int = 0
    actions: list = field(default_factory=lambda: [Action(damage=13)])

    def next(self) -> Intent:
        return SpinningKick()

@dataclass(repr=False)
class SpinningKick(Intent):
    id: int = 1
    actions: list = field(default_factory=lambda: [Action(damage=2) for _ in range(4)])

    def next(self) -> Intent:
        return BubbleBurp()

@dataclass(repr=False)
class BubbleBurp(Intent):
    id: int = 2
    actions: list = field(default_factory=lambda: [Action(block=8, buffs=[Strength(power=2)])])

    def next(self) -> Intent:
        return SeaKick()

@dataclass(repr=False)
class Seapunk(Enemy):
    id: int = 5
    intent: Intent = field(default_factory=SeaKick)
    min_hp = 47
    max_hp = 49
