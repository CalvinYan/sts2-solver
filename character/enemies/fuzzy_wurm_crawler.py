from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effects import Strength

@dataclass(repr=False)
class AcidGoop1(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=6, block=0)])
    
    def next(self) -> Intent:
        return Inhale()

@dataclass(repr=False)
class Inhale(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=0, block=0, buffs=[Strength(power=7)])])
    
    def next(self) -> Intent:
        return AcidGoop2()

@dataclass(repr=False)
class AcidGoop2(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=6, block=0)])
    
    def next(self) -> Intent:
        return AcidGoop1()

@dataclass(repr=False)
class FuzzyWurmCrawler(Enemy):
    intent: Intent = field(default_factory=AcidGoop1)
    min_hp: int = 58
    max_hp: int = 59
