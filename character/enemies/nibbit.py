from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Strength


@dataclass(frozen=True)
class Butt(Intent):
    id: int = 0

    def actions(self) -> list[Action]:
        return [Action(damage=13)]

    def next(self) -> Intent:
        return HesitantSlice()


@dataclass(frozen=True)
class HesitantSlice(Intent):
    id: int = 1

    def actions(self) -> list[Action]:
        return [Action(damage=7, block=6)]

    def next(self) -> Intent:
        return Hiss()


@dataclass(frozen=True)
class Hiss(Intent):
    id: int = 2

    def actions(self) -> list[Action]:
        return [Action(actor_effects=[Strength(power=3)])]

    def next(self) -> Intent:
        return Butt()


@dataclass
class Nibbit(Enemy):
    id: int = 4
    intent: Intent = field(default_factory=Butt)
    min_hp: int = 44
    max_hp: int = 48
