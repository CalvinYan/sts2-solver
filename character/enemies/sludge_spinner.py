from dataclasses import dataclass, field
from fractions import Fraction
from random import random

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Strength, Weak

@dataclass
class OilSpray(Intent):
    id: int = 0
    actions: list = field(default_factory=lambda: [Action(damage=9, debuffs=[Weak(duration=1)])])

    def next(self) -> Intent:
        return Slam() if random() < 0.5 else Rage()

    def next_intents(self) -> list[Intent, Fraction]:
        return [(Slam(), Fraction(1, 2)), (Rage(), Fraction(1, 2))]

@dataclass
class Slam(Intent):
    id: int = 1
    actions: list = field(default_factory=lambda: [Action(damage=12)])

    def next(self) -> Intent:
        return OilSpray() if random() < 0.5 else Rage()

    def next_intents(self) -> list[Intent, Fraction]:
        return [(OilSpray(), Fraction(1, 2)), (Rage(), Fraction(1, 2))]

@dataclass
class Rage(Intent):
    id: int = 2
    actions: list = field(default_factory=lambda: [Action(damage=7, buffs=[Strength(power=3)])])

    def next(self) -> Intent:
        return OilSpray() if random() < 0.5 else Slam()

    def next_intents(self) -> list[Intent, Fraction]:
        return [(OilSpray(), Fraction(1, 2)), (Slam(), Fraction(1, 2))]

@dataclass
class SludgeSpinner(Enemy):
    id: int = 7
    intent: Intent = field(default_factory=OilSpray)
    min_hp = 41
    max_hp = 42
