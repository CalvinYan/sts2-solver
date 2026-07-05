from __future__ import annotations

from dataclasses import dataclass, field
from random import randint
from typing import ClassVar

from character.core import Character
from util.core import Action

@dataclass(repr=False)
class Intent:
    """A sequence of actions that an enemy will perform on a given turn, with a random variable determining its next intent."""
    id: int
    actions: list[Action]

    def next(self) -> Intent:
        pass

    def to_vector(self) -> tuple:
        return (self.id,)

    def __repr__(self) -> str:
        return type(self).__name__

@dataclass(kw_only=True, repr=False)
class Enemy(Character):
    """
    A hostile non-player character with an intent and a range of possible hp values.
    Each fight starts with one or more enemies, and ends if none remain with more than 0 HP.
    """
    hp: int = field(init=False)

    intent: Intent
    min_hp: ClassVar[int]
    max_hp: ClassVar[int]

    def __post_init__(self):
        self.hp = randint(self.min_hp, self.max_hp)

    def resolve_turn(self, fight: "Fight") -> None:
        for action in self.intent.actions:
            self.act(target=fight.player, action=action) # Doesn't handle dying mid-turn but that will never happen Floor 2
        return True

    def resolve_end_of_turn(self, fight: "Fight") -> None:
        super().resolve_end_of_turn(fight)
        self.intent = self.intent.next()
    
    # Vector representation of an Enemy for interpretation by learning models.
    # The representation is defined in the following way:
    # - 0 if the enemy does not exist, 1 if it does. This is necessary because Fight encodes a fixed # of enemies to
    #   maintain constant vector length
    # - the Character vector for the enemy
    # - the id of the enemy's intent
    #
    # A nonexistent enemy (None) is encoded as all zeroes.
    def to_vector(self) -> tuple:
        if self is None:
            return (0,) + Character.to_vector(None) + (0,)
        return (1,) + super().to_vector() + self.intent.to_vector()

    def __repr__(self):
        return super().__repr__() + f" {self.intent}"