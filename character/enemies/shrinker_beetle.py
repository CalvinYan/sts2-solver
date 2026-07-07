from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Shrink

@dataclass
class Shrinker(Intent):
    id: int = 0
    actions: list = field(default_factory=lambda: [Action(debuffs=[Shrink()])])

    def next(self) -> Intent:
        return Chomp()

@dataclass
class Chomp(Intent):
    id: int = 1
    actions: list = field(default_factory=lambda: [Action(damage=8)])

    def next(self) -> Intent:
        return Stomp()

@dataclass
class Stomp(Intent):
    id: int = 2
    actions: list = field(default_factory=lambda: [Action(damage=14)])

    def next(self) -> Intent:
        return Chomp()

@dataclass
class ShrinkerBeetle(Enemy):
    id: int = 6
    intent: Intent = field(default_factory=Shrinker)
    min_hp = 40
    max_hp = 42
