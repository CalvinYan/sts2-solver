from __future__ import annotations

import itertools
import random

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

import numpy as np

from util.core import Action
from util.effect import Vulnerable

class Targeting(Enum):
    NONE = 0
    ENEMY_SINGLE = 1
    ALLY_SINGLE = 2

@dataclass(frozen=True)
class Card:
    """An action with an energy cost and a target type."""
    id: int
    action: Action
    cost: int
    targeting: Targeting

    def playable(self, energy: int) -> bool:
        return energy >= self.cost

    def to_vector(self) -> np.ndarray:
        base = np.zeros(max(ID_TO_CARD.keys()) + 1, dtype=int)
        if self is not None:
            base[self.id] = 1
        return base

    def __str__(self):
        return type(self).__name__

    def __deepcopy__(self, memo) -> Card:
        return self

@dataclass(frozen=True)
class Strike(Card):
    id: int = 0
    action: Action = field(default_factory=lambda: Action(damage=6))
    cost: int = 1
    targeting: Targeting = Targeting.ENEMY_SINGLE

@dataclass(frozen=True)
class Defend(Card):
    id: int = 1
    action: Action = field(default_factory=lambda: Action(block=5))
    cost: int = 1
    targeting: Targeting = Targeting.NONE

@dataclass(frozen=True)
class Bash(Card):
    id: int = 2
    action: Action = field(default_factory=lambda: Action(damage=8, debuffs=[Vulnerable(duration=2)]))
    cost: int = 2
    targeting: Targeting = Targeting.ENEMY_SINGLE

@dataclass(frozen=True)
class AscendersBane(Card):
    id: int = 11
    action: Action = field(default_factory=lambda: Action())
    cost: int = None
    targeting: Targeting = Targeting.NONE

    def playable(self, energy: int) -> bool:
        return False

ID_TO_CARD = {
    Strike.id: Strike,
    Defend.id: Defend,
    Bash.id: Bash,
    AscendersBane.id: AscendersBane
}

# An abstraction for a pile of cards, such as the player's hand, draw pile, and discard pile.
@dataclass()
class CardPile():
    cards: Counter[Card] = field(default_factory=Counter)

    def pop(self) -> Card:
        if not self.cards:
            return None
        card = random.choice(list(self.cards.elements()))
        self.cards[card] -= 1
        if self.cards[card] == 0:
            del self.cards[card]

        return card

    def draw(self, source: CardPile):
        card = source.pop()
        if card is not None:
            self.cards[card] += 1

    # Helper method for dp solve. Computes the probability distribution of drawing n cards from this pile.
    def next_hands(self, cards: int) -> list[CardPile, Fraction]:
        if cards > self.cards.total():
            raise ValueError(f"Cannot draw {cards} cards from a pile of {self.cards.total()}")

        # A neat one-liner that determines each possible permutation and the number of ways to reach it
        combinations = Counter(itertools.combinations(self.cards.elements(), cards))

        # Convert tuples to CardPiles and counts to probabilities
        return [(CardPile(cards=Counter(k)), Fraction(v, sum(combinations.values()))) for k, v in combinations.items()]

    def to_vector(self) -> np.ndarray:
        return sum([card.to_vector() * count for card, count in self.cards.items()], start=Card.to_vector(None))
    
    def __add__(self, other: CardPile):
        if type(other) is not CardPile:
            raise TypeError("Cannot add card pile and", type(other))

        return CardPile(cards=self.cards + other.cards)

    def __sub__(self, other: CardPile):
        if type(other) is not CardPile:
            raise TypeError("Cannot subtract card pile and", type(other))

        return CardPile(cards=self.cards - other.cards)

    def __str__(self):
        return f"[{" ".join([str(card) for card in self.cards.elements()])}]"
