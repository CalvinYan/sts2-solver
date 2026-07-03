from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effects import Shrink

@dataclass(repr=False)
class Shrinker(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=0, block=0, debuffs=[Shrink()])])
    
    def next(self) -> Intent:
        return Chomp()

@dataclass(repr=False)
class Chomp(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=8, block=0)])
    
    def next(self) -> Intent:
        return Stomp()

@dataclass(repr=False)
class Stomp(Intent):
    actions: list = field(default_factory=lambda: [Action(damage=14, block=0)])
    
    def next(self) -> Intent:
        return Chomp()

@dataclass(repr=False)
class ShrinkerBeetle(Enemy):
    intent: Intent = field(default_factory=Shrinker)
    min_hp = 40
    max_hp = 42
