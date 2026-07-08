from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Shrink


@dataclass(frozen=True)
class Shrinker(Intent):
    id: int = 0

    def actions(self) -> list[Action]:
        return [Action(debuffs=[Shrink()])]

    def next(self) -> Intent:
        return Chomp()


@dataclass(frozen=True)
class Chomp(Intent):
    id: int = 1

    def actions(self) -> list[Action]:
        return [Action(damage=8)]

    def next(self) -> Intent:
        return Stomp()


@dataclass(frozen=True)
class Stomp(Intent):
    id: int = 2

    def actions(self) -> list[Action]:
        return [Action(damage=14)]

    def next(self) -> Intent:
        return Chomp()


@dataclass
class ShrinkerBeetle(Enemy):
    id: int = 6
    intent: Intent = field(default_factory=Shrinker)
    min_hp: int = 40
    max_hp: int = 42
