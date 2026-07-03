from dataclasses import dataclass

from enemy import Enemy, Intent
from util.core import Action
from util.effects import Strength

@dataclass
class AcidGoop1(Intent):
    actions = [Action(damage=6, block=0)]
    
    def next(self) -> Intent:
        return Inhale()

@dataclass
class Inhale(Intent):
    actions = [Action(damage=0, block=0, buffs=[Strength(power=7)])]
    
    def next(self) -> Intent:
        return AcidGoop2()

@dataclass
class AcidGoop2(Intent):
    actions = [Action(damage=6, block=0)]
    
    def next(self) -> Intent:
        return AcidGoop1()

@dataclass
class FuzzyWurmCrawler(Enemy):
    intent = AcidGoop1()
    min_hp = 58
    max_hp = 59
