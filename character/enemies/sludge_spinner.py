from dataclasses import dataclass, field
from fractions import Fraction
from random import random

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Strength, Weak

@dataclass(frozen=True)
class OilSpray(Intent):
    id: int = 0

    def actions(self) -> list[Action]:
        return [Action(damage=9, debuffs=[Weak(duration=1)])]

    def next(self) -> Intent:
        return Slam() if random() < 0.5 else Rage()

    def next_intents(self) -> list[tuple[Intent, Fraction]]:
        return [(Slam(), Fraction(1, 2)), (Rage(), Fraction(1, 2))]

@dataclass(frozen=True)
class Slam(Intent):
    id: int = 1

    def actions(self) -> list[Action]:
        return [Action(damage=12)]

    def next(self) -> Intent:
        return OilSpray() if random() < 0.5 else Rage()

    def next_intents(self) -> list[tuple[Intent, Fraction]]:
        return [(OilSpray(), Fraction(1, 2)), (Rage(), Fraction(1, 2))]

@dataclass(frozen=True)
class Rage(Intent):
    id: int = 2

    def actions(self) -> list[Action]:
        return [Action(damage=7, buffs=[Strength(power=3)])]

    def next(self) -> Intent:
        return OilSpray() if random() < 0.5 else Slam()

    def next_intents(self) -> list[tuple[Intent, Fraction]]:
        return [(OilSpray(), Fraction(1, 2)), (Slam(), Fraction(1, 2))]

@dataclass
class SludgeSpinner(Enemy):
    id: int = 7
    intent: Intent = field(default_factory=OilSpray)
    min_hp: int = 41
    max_hp: int = 42
