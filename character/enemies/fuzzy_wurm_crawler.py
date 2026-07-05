from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Strength

@dataclass(repr=False)
class AcidGoop1(Intent):
    id: int = 0
    actions: list = field(default_factory=lambda: [Action(damage=6)])
    
    def next(self) -> Intent:
        return Inhale()

@dataclass(repr=False)
class Inhale(Intent):
    id: int = 1
    actions: list = field(default_factory=lambda: [Action(buffs=[Strength(power=7)])])
    
    def next(self) -> Intent:
        return AcidGoop2()

@dataclass(repr=False)
class AcidGoop2(Intent):
    id: int = 2
    actions: list = field(default_factory=lambda: [Action(damage=6)])
    
    def next(self) -> Intent:
        return AcidGoop1()

@dataclass(repr=False)
class FuzzyWurmCrawler(Enemy):
    id: int = 1
    intent: Intent = field(default_factory=AcidGoop1)
    min_hp: int = 58
    max_hp: int = 59
