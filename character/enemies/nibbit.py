from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effects import Strength

@dataclass
class Butt(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=13, block=0)])
    
    def next(self) -> Intent:
        return HesitantSlice()

@dataclass
class HesitantSlice(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=7, block=6)])
    
    def next(self) -> Intent:
        return Hiss()

@dataclass
class Hiss(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=0, block=0, buffs=[Strength(power=3)])])
    
    def next(self) -> Intent:
        return Butt()

@dataclass
class Nibbit(Enemy):
    intent: Intent = field(default_factory=Butt)
    min_hp = 44
    max_hp = 48
