from dataclasses import dataclass
from random import random

from enemy import Enemy, Intent
from util.core import Action
from util.effects import Strength, Weak

@dataclass
class OilSpray(Intent):
    actions = [Action(damage=9, block=0, debuffs=[Weak(duration=1)])]
    
    def next(self) -> Intent:
        return Slam() if random() < 0.5 else Rage()

@dataclass
class Slam(Intent):
    actions = [Action(damage=12, block=0)]
    
    def next(self) -> Intent:
        return OilSpray() if random() < 0.5 else Rage()

@dataclass
class Rage(Intent):
    actions = [Action(damage=7, block=0, buffs=[Strength(power=3)])]
    
    def next(self) -> Intent:
        return OilSpray() if random() < 0.5 else Slam()

@dataclass
class SludgeSpinner(Enemy):
    intent = OilSpray()
    min_hp = 41
    max_hp = 42
