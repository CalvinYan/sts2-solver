"""Contains data abstractions for cards, piles of cards, and the library of cards itself."""

from __future__ import annotations

import itertools
import random
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction

import numpy as np

from util.core import Action
from util.effect import Vulnerable, Weak


class Targeting(Enum):
    NONE = 0
    ENEMY_SINGLE = 1
    ALLY_SINGLE = 2


@dataclass(frozen=True)
class Card:
    """An action with an energy cost and a target type."""

    id: int
    cost: int | None
    targeting: Targeting

    def action(self) -> Action:
        return Action()

    def playable(self, energy: int) -> bool:
        return self.cost is not None and energy >= self.cost

    def to_vector(self: Card | None) -> np.ndarray:
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
    cost: int = 1
    targeting: Targeting = Targeting.ENEMY_SINGLE

    def action(self) -> Action:
        return Action(damage=6)


@dataclass(frozen=True)
class Defend(Card):
    id: int = 1
    cost: int = 1
    targeting: Targeting = Targeting.NONE

    def action(self) -> Action:
        return Action(block=5)


@dataclass(frozen=True)
class Bash(Card):
    id: int = 2
    cost: int = 2
    targeting: Targeting = Targeting.ENEMY_SINGLE

    def action(self) -> Action:
        return Action(damage=8, target_effects=[Vulnerable(duration=2)])


@dataclass(frozen=True)
class Neutralize(Card):
    id: int = 3
    cost: int = 0
    targeting: Targeting = Targeting.ENEMY_SINGLE

    def action(self) -> Action:
        return Action(damage=3, target_effects=[Weak(duration=1)])


@dataclass(frozen=True)
class Survivor(Card):
    id: int = 4
    cost: int = 1
    targeting: Targeting = Targeting.NONE

    def action(self) -> Action:
        return Action(block=8)


@dataclass(frozen=True)
class Venerate(Card):
    id: int = 5
    cost: int = 1
    targeting: Targeting = Targeting.NONE


@dataclass(frozen=True)
class FallingStar(Card):
    id: int = 6
    cost: int = 0
    star_cost: int = 2
    targeting: Targeting = Targeting.ENEMY_SINGLE

    def action(self) -> Action:
        return Action(damage=8, target_effects=[Weak(duration=1), Vulnerable(duration=1)])


@dataclass(frozen=True)
class Bodyguard(Card):
    id: int = 7
    cost: int = 1
    targeting: Targeting = Targeting.NONE


@dataclass(frozen=True)
class Unleash(Card):
    id: int = 8
    cost: int = 1
    targeting: Targeting = Targeting.ENEMY_SINGLE


@dataclass(frozen=True)
class Zap(Card):
    id: int = 9
    cost: int = 1
    targeting: Targeting = Targeting.NONE


@dataclass(frozen=True)
class Dualcast(Card):
    id: int = 10
    cost: int = 1
    targeting: Targeting = Targeting.NONE


@dataclass(frozen=True)
class AscendersBane(Card):
    id: int = 11
    cost: None = None
    targeting: Targeting = Targeting.NONE


ID_TO_CARD = {
    Strike.id: Strike,
    Defend.id: Defend,
    Bash.id: Bash,
    AscendersBane.id: AscendersBane,
}


# An abstraction for a pile of cards, such as the player's hand, draw pile, and discard pile.
@dataclass()
class CardPile:
    cards: Counter[Card] = field(default_factory=Counter)

    def pop(self) -> Card | None:
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
    def next_hands(self, cards: int) -> list[tuple[CardPile, Fraction]]:
        if cards > self.cards.total():
            raise ValueError(f"Cannot draw {cards} cards from a pile of {self.cards.total()}")

        # A neat one-liner that determines each possible permutation and the number of ways to reach it
        combinations = Counter(itertools.combinations(self.cards.elements(), cards))

        # Convert tuples to CardPiles and counts to probabilities
        return [(CardPile(cards=Counter(k)), Fraction(v, sum(combinations.values()))) for k, v in combinations.items()]

    def to_vector(self) -> np.ndarray:
        return sum(
            [card.to_vector() * count for card, count in self.cards.items()],
            start=Card.to_vector(None),
        )

    @staticmethod
    def from_vector(vector: tuple[int, ...]) -> tuple[CardPile, int]:
        min_length = max(ID_TO_CARD) + 1
        if len(vector) < min_length:
            raise ValueError(f"Not enough values CardPile vector: expected {min_length}, got {len(vector)}")

        cards: Counter[Card] = Counter()
        for card_id, cnt in enumerate(vector[:min_length]):
            if cnt > 0:
                cards[ID_TO_CARD[card_id]()] = cnt

        return CardPile(cards=cards), min_length

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
