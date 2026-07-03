from dataclasses import dataclass, field
from random import random

from character.enemy import Enemy, Intent
from util.core import Action
from util.effects import Strength, Weak

@dataclass(repr=False)
class OilSpray(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=9, block=0, debuffs=[Weak(duration=1)])])
    
    def next(self) -> Intent:
        return Slam() if random() < 0.5 else Rage()

@dataclass(repr=False)
class Slam(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=12, block=0)])
    
    def next(self) -> Intent:
        return OilSpray() if random() < 0.5 else Rage()

@dataclass(repr=False)
class Rage(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=7, block=0, buffs=[Strength(power=3)])])
    
    def next(self) -> Intent:
        return OilSpray() if random() < 0.5 else Slam()

@dataclass(repr=False)
class SludgeSpinner(Enemy):
    intent: Intent = field(default_factory=OilSpray)
    min_hp = 41
    max_hp = 42
