from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Strength

@dataclass(frozen=True)
class AcidGoop1(Intent):
    id: int = 0

    def actions(self) -> list[Action]:
        return [Action(damage=6)]
    
    def next(self) -> Intent:
        return Inhale()

@dataclass(frozen=True)
class Inhale(Intent):
    id: int = 1

    def actions(self) -> list[Action]:
        return [Action(buffs=[Strength(power=7)])]

    def next(self) -> Intent:
        return AcidGoop2()

@dataclass(frozen=True)
class AcidGoop2(Intent):
    id: int = 2

    def actions(self) -> list[Action]:
        return [Action(damage=6)]

    def next(self) -> Intent:
        return AcidGoop1()

@dataclass
class FuzzyWurmCrawler(Enemy):
    id: int = 1
    intent: Intent = field(default_factory=AcidGoop1)
    min_hp: int = 58
    max_hp: int = 59
