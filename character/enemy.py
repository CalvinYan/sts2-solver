from dataclasses import dataclass, field
from random import randint
from typing import ClassVar

from core import Character
from fight import Fight
from util.core import Action

@dataclass
class Intent:
    """A sequence of actions that an enemy will perform on a given turn, with a random variable determining its next intent."""
    actions: list[Action]

    def next(self) -> Intent:
        pass

@dataclass
class Enemy(Character):
    """
    A hostile non-player character with an intent and a range of possible hp values.
    Each fight starts with one or more enemies, and ends if none remain with more than 0 HP.
    """
    hp = field(init=False)

    intent: Intent
    min_hp: ClassVar[int]
    max_hp: ClassVar[int]

    def __post_init__(self):
        self.hp = randint(self.min_hp, self.max_hp)

    def resolve_turn(self, fight: Fight) -> None:
        for action in self.intent.actions:
            self.act(target=self.target, action=action) # Doesn't handle dying mid-turn but that will never happen Floor 2
        return True

    def resolve_end_of_turn(self, fight: Fight) -> None:
        super().resolve_end_of_turn(fight)
        self.intent = self.intent.next()
