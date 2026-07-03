from dataclasses import dataclass

from enemy import Enemy, Intent
from util import Action
from util.effects import Strength

@dataclass
class SeaKick(Intent):
    actions = [Action(damage=13, block=0)]
    
    def next(self) -> Intent:
        return SpinningKick()

@dataclass
class SpinningKick(Intent):
    actions = [Action(damage=2, block=0)] * 4
    
    def next(self) -> Intent:
        return BubbleBurp()

@dataclass
class BubbleBurp(Intent):
    actions = [Action(damage=0, block=8, buffs=[Strength(power=2)])]
    
    def next(self) -> Intent:
        return SeaKick()

@dataclass
class Seapunk(Enemy):
    intent = SeaKick()
    min_hp = 47
    max_hp = 49
