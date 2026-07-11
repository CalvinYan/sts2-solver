"""Defines player behavior and the five player classes."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING, Callable

from card import (
    AscendersBane,
    Bash,
    Bodyguard,
    Card,
    CardPile,
    Defend,
    Dualcast,
    FallingStar,
    Neutralize,
    Strike,
    Survivor,
    Unleash,
    Venerate,
    Zap,
)
from character.core import Character

if TYPE_CHECKING:
    from fight import Fight


@dataclass(kw_only=True, repr=False)
class Player(Character):
    """
    A player-controlled character with the cards in their deck distributed between their hand, draw pile, and discard pile.
    Each fight has exactly one player.
    """

    energy: int = 3
    hand: CardPile = field(default_factory=CardPile)
    draw_pile: CardPile
    discard_pile: CardPile = field(default_factory=CardPile)

    # TODO: Expose this as an overrideable method instead of a field
    player_turn_callback: Callable[[Fight], bool] | None

    def draw(self, cards: int) -> None:
        for _ in range(cards):
            if self.hand.cards.total() >= 10:
                print("Hand is full")
                return

            if not self.draw_pile.cards:
                self.draw_pile.cards = self.discard_pile.cards
                self.discard_pile = CardPile()

            self.hand.draw(self.draw_pile)

    def can_play(self, card: Card) -> bool:
        return card.cost is not None and self.energy >= card.cost

    def play(self, card: Card, target: Character | None = None) -> None:
        if self.hand.cards[card] == 0:
            print(f"{self.name} tried to play {card} but hand is: {self.hand}")
            return

        if not self.can_play(card):
            print(f"{self.name} tried to play {card} but card is not playable")
            return

        self.act(target=target, action=card.action())

        self.energy -= card.cost  # type: ignore

        self.hand.cards[card] -= 1
        if self.hand.cards[card] == 0:
            del self.hand.cards[card]

        self.discard_pile.cards[card] += 1

    def resolve_start_of_turn(self) -> None:
        super().resolve_start_of_turn()
        self.energy = 3
        self.draw(5)

    def resolve_turn(self, fight: Fight) -> bool:
        return self.player_turn_callback(fight) if self.player_turn_callback else True

    def resolve_end_of_turn(self) -> None:
        super().resolve_end_of_turn()

        if self.hand.cards[AscendersBane()] > 0:
            del self.hand.cards[AscendersBane()]

        self.discard_pile += self.hand
        self.hand = CardPile()

    # Helper method for dp solve - computes all possible next states of the player and their probabilities.
    # For our purposes, this calculation is only nontrivial when the player is drawing cards, so this method
    # primarily calculates draw order probabilities.
    def next_states(self) -> list[tuple[Player, Fraction]]:
        clone = deepcopy(self)
        clone.resolve_end_of_turn()

        cards_drawn = 5
        result = []

        if cards_drawn > clone.draw_pile.cards.total():
            reshuffle_draws = clone.discard_pile.next_hands(
                cards=min(
                    clone.discard_pile.cards.total(),
                    cards_drawn - self.draw_pile.cards.total(),
                )
            )

            for draw, probability in reshuffle_draws:
                future_player = deepcopy(clone)
                future_player.draw_pile = clone.discard_pile - draw
                future_player.hand = clone.draw_pile + draw
                future_player.discard_pile = CardPile()

                result.append((future_player, probability))
        else:
            hands = clone.draw_pile.next_hands(cards_drawn)

            for hand, probability in hands:
                future_player = deepcopy(clone)
                future_player.draw_pile = clone.draw_pile - hand
                future_player.hand = hand
                future_player.discard_pile = clone.discard_pile

                result.append((future_player, probability))

        return result

    def to_vector(self) -> list[int]:
        return [
            *super().to_vector(),
            self.energy,
            *self.draw_pile.to_vector(),
            *self.hand.to_vector(),
            *self.discard_pile.to_vector(),
        ]

    def read_vector(self, vector: tuple[int, ...]) -> int:
        values_read = 0
        try:
            read = super().read_vector(vector)
            values_read += read
        except ValueError as e:
            raise ValueError("Error reading Character from Player vector:", e)

        if len(vector) < values_read + 1:
            raise ValueError(
                f"Could not read energy from Player vector: expected {values_read + 1} values, got {len(vector)}"
            )
        self.energy = vector[values_read]
        values_read += 1

        for pile, name in zip([self.draw_pile, self.hand, self.discard_pile], ["draw pile", "hand", "discard pile"]):
            read = pile.read_vector(vector[values_read:])
            values_read += read

        return values_read

    @staticmethod
    def from_vector(vector: tuple[int, ...]) -> tuple[Player, int]:
        # TODO: Make draw_pile() empty by default

        # hp is intentionally omitted so the subclass's default applies;
        # mypy can't know that every registered subclass defines those defaults.
        player = ID_TO_PLAYER[vector[0]](name="Player", id=0, player_turn_callback=None, draw_pile=CardPile())  # type: ignore[call-arg]
        read = player.read_vector(vector)
        return player, read

    def __str__(self) -> str:
        return f"{super().__str__()}\nHand: {self.hand}\nDraw: {self.draw_pile}\nDiscard: {self.discard_pile}"


@dataclass
class Ironclad(Player):
    id: int = 0
    hp: int = 64
    draw_pile: CardPile = field(
        default_factory=lambda: CardPile(
            cards=Counter(
                {
                    Strike(): 5,
                    Defend(): 4,
                    Bash(): 1,
                    AscendersBane(): 1,
                }
            )
        )
    )


@dataclass
class Silent(Player):
    id: int = 0
    hp: int = 56
    draw_pile: CardPile = field(
        default_factory=lambda: CardPile(
            cards=Counter(
                {
                    Strike(): 5,
                    Defend(): 5,
                    Neutralize(): 1,
                    Survivor(): 1,
                    AscendersBane(): 1,
                }
            )
        )
    )


@dataclass
class Regent(Player):
    id: int = 0
    hp: int = 60
    draw_pile: CardPile = field(
        default_factory=lambda: CardPile(
            cards=Counter(
                {
                    Strike(): 4,
                    Defend(): 4,
                    Venerate(): 1,
                    FallingStar(): 1,
                    AscendersBane(): 1,
                }
            )
        )
    )


@dataclass
class Necrobinder(Player):
    id: int = 0
    hp: int = 52
    draw_pile: CardPile = field(
        default_factory=lambda: CardPile(
            cards=Counter(
                {
                    Strike(): 4,
                    Defend(): 4,
                    Bodyguard(): 1,
                    Unleash(): 1,
                    AscendersBane(): 1,
                }
            )
        )
    )


@dataclass
class Defect(Player):
    id: int = 4
    hp: int = 60
    draw_pile: CardPile = field(
        default_factory=lambda: CardPile(
            cards=Counter(
                {
                    Strike(): 4,
                    Defend(): 4,
                    Zap(): 1,
                    Dualcast(): 1,
                    AscendersBane(): 1,
                }
            )
        )
    )


ID_TO_PLAYER: dict[int, type[Player]] = {Ironclad.id: Ironclad}
