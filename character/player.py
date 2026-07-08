from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable

from card import AscendersBane, Bash, Card, CardPile, Defend, Strike
from character.core import Character


@dataclass(kw_only=True, repr=False)
class Player(Character):
    """
    A player-controlled character with the cards in their deck distributed between their hand, draw pile, and discard pile.
    Each fight has exactly one player.
    """

    hp: int
    energy: int = 3
    hand: CardPile = field(default_factory=CardPile)
    draw_pile: CardPile
    discard_pile: CardPile = field(default_factory=CardPile)

    player_turn_callback: Callable[["Fight"], bool]  # type: ignore

    def draw(self, cards: int) -> None:
        for _ in range(cards):
            if self.hand.cards.total() >= 10:
                print("Hand is full")
                return

            if not self.draw_pile.cards:
                self.draw_pile.cards = self.discard_pile.cards
                self.discard_pile = CardPile()

            self.hand.draw(self.draw_pile)

    def play(self, card: Card, target: Character | None = None) -> None:
        if self.hand.cards[card] == 0:
            print(f"{self.name} tried to play {card} but hand is: {self.hand}")
            return

        if not card.playable(self.energy):
            print(f"{self.name} tried to play {card} but card is not playable")
            return

        self.act(target=target, action=card.action())

        self.energy -= card.cost  # type: ignore

        self.hand.cards[card] -= 1
        if self.hand.cards[card] == 0:
            del self.hand.cards[card]

        self.discard_pile.cards[card] += 1

    def resolve_start_of_turn(self, fight: "Fight") -> None:  # type: ignore
        super().resolve_start_of_turn(fight)
        self.energy = 3
        self.draw(5)

    def resolve_turn(self, fight: "Fight") -> bool:  # type: ignore
        return self.player_turn_callback(fight)

    def resolve_end_of_turn(self, fight: "Fight") -> None:  # type: ignore
        super().resolve_end_of_turn(fight)

        if self.hand.cards[AscendersBane()] > 0:
            del self.hand.cards[AscendersBane()]

        self.discard_pile += self.hand
        self.hand = CardPile()

    # Helper method for dp solve - computes all possible next states of the player and their probabilities.
    # For our purposes, this calculation is only nontrivial when the player is drawing cards, so this method
    # primarily calculates draw order probabilities.
    def next_states(self) -> list[tuple[Player, Fraction]]:
        clone = deepcopy(self)
        clone.resolve_end_of_turn(None)

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
