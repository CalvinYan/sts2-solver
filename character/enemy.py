from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from random import randint
from typing import TYPE_CHECKING

import numpy as np

from character.core import Character
from util.core import Action

if TYPE_CHECKING:
    from fight import Fight


@dataclass(frozen=True)
class Intent:
    """A sequence of actions that an enemy will perform on a given turn, with a random variable determining its next intent."""

    id: int

    def actions(self) -> list[Action]:
        return list()

    def next(self) -> Intent:
        return Intent(id=0)

    # Helper method for dp solve. Returns the probability distribtion of the next intent after this one
    def next_intents(self) -> list[tuple[Intent, Fraction]]:
        return [(self.next(), Fraction(1, 1))]

    def to_vector(self) -> np.ndarray:
        return np.array([self.id])

    def __str__(self) -> str:
        return type(self).__name__

    def __deepcopy__(self, memo) -> Intent:
        return self


@dataclass(kw_only=True)
class Enemy(Character):
    """
    A hostile non-player character with an intent and a range of possible hp values.
    Each fight starts with one or more enemies, and ends if none remain with more than 0 HP.
    """

    # TODO: Find a neater way to do this
    hp: int = 0
    intent: Intent
    min_hp: int
    max_hp: int

    def __post_init__(self):
        if self.hp == 0:
            self.hp = randint(self.min_hp, self.max_hp)

    def resolve_turn(self, fight: Fight) -> bool:
        for action in self.intent.actions():
            self.act(
                target=fight.player, action=action
            )  # Doesn't handle dying mid-turn but that will never happen Floor 2
        return True

    def resolve_end_of_turn(self) -> None:
        super().resolve_end_of_turn()
        self.intent = self.intent.next()

    # Helper method for dp solve.
    # Computes the probability distribution of an enemy's state during the start of the player's next turn.
    # For our case, the only source of randomness is the enemy's next intent, so this just returns the probability
    # distrubtion of next intents.
    def next_states(self) -> list[tuple[Enemy, Fraction]]:
        result = []
        for intent, probability in self.intent.next_intents():
            clone = deepcopy(self)
            # TODO: I dislike this way of copying objects for next states... using setter methods would be much more Pythonic
            clone.intent = intent
            result.append((clone, probability))

        return result

    # Vector representation of an Enemy for interpretation by learning models.
    # The representation is defined in the following way:
    # - 0 if the enemy does not exist, 1 if it does. This is necessary because Fight encodes a fixed # of enemies to
    #   maintain constant vector length
    # - the Character vector for the enemy
    # - the id of the enemy's intent
    #
    # A nonexistent enemy (None) is encoded as all zeroes.
    # TODO: This signature override is disgusting. Find another way to do it
    def to_vector(self: Enemy | None) -> np.ndarray:
        if self is None:
            return np.concatenate([[0], Character.to_vector(None), [0]])
        return np.concatenate([[1], super(Enemy, self).to_vector(), self.intent.to_vector()])

    def __str__(self):
        return super().__str__() + f" {self.intent}"
