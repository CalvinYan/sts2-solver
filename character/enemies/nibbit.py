from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effects import Strength

@dataclass(repr=False)
class Butt(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=13)])
    
    def next(self) -> Intent:
        return HesitantSlice()

@dataclass(repr=False)
class HesitantSlice(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=7, block=6)])
    
    def next(self) -> Intent:
        return Hiss()

@dataclass(repr=False)
class Hiss(Intent):
    actions: list = field(default_factory=lambda: [Action(buffs=[Strength(power=3)])])
    
    def next(self) -> Intent:
        return Butt()

@dataclass(repr=False)
class Nibbit(Enemy):
    intent: Intent = field(default_factory=Butt)
    min_hp = 44
    max_hp = 48
