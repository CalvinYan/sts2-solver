from dataclasses import dataclass

from character.enemy import Enemy, Intent
from util.core import Action
from util.effects import Shrink

@dataclass
class Shrinker(Intent):
    actions = [Action(damage=0, block=0, debuffs=[Shrink()])]
    
    def next(self) -> Intent:
        return Chomp()

@dataclass
class Chomp(Intent):
    actions = [Action(damage=8, block=0)]
    
    def next(self) -> Intent:
        return Stomp()

@dataclass
class Stomp(Intent):
    actions = [Action(damage=14, block=0)]
    
    def next(self) -> Intent:
        return Chomp()

@dataclass
class ShrinkerBeetle(Enemy):
    intent = Shrinker()
    min_hp = 40
    max_hp = 42
