from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effects import Strength

@dataclass
class SeaKick(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=13, block=0)])
    
    def next(self) -> Intent:
        return SpinningKick()

@dataclass
class SpinningKick(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=2, block=0) for _ in range(4)])
    
    def next(self) -> Intent:
        return BubbleBurp()

@dataclass
class BubbleBurp(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=0, block=8, buffs=[Strength(power=2)])])
    
    def next(self) -> Intent:
        return SeaKick()

@dataclass
class Seapunk(Enemy):
    intent: Intent = field(default_factory=SeaKick)
    min_hp = 47
    max_hp = 49
