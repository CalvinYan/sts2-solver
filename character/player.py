from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

from card import AscendersBane, Bash, Card, CardPile, Defend, Strike
from character.core import Character

@dataclass(kw_only=True, repr=False)
class Player(Character):
    """
    A player-controlled character with the cards in their deck distributed between their hand, draw pile, and discard pile.
    Each fight has exactly one player.
    """
    # We don't care about the player's HP, only how much they lose during the fight
    hp: int = 0
    energy: int = 3
    hand: CardPile = field(default_factory=CardPile)
    draw_pile: CardPile
    discard_pile: CardPile = field(default_factory=CardPile)

    player_turn_callback: Callable[["Fight"], bool]

    def draw(self, cards: int) -> None:
        for _ in range(cards):
            if self.hand.cards.total() >= 10:
                print("Hand is full")
                return

            if not self.draw_pile.cards:
                self.draw_pile.cards = self.discard_pile.cards
                self.discard_pile = CardPile()

            self.hand.draw(self.draw_pile)

    def play(self, card: Card, target: Character = None) -> None:
        if self.hand.cards[card] == 0:
            print("Card not in hand")
            return

        self.act(target=target, action=card.action)

        self.energy -= card.cost

        self.hand.cards[card] -= 1
        if self.hand.cards[card] == 0:
            del self.hand.cards[card]

        self.discard_pile.cards[card] += 1

    def resolve_start_of_turn(self, fight: "Fight") -> None:
        super().resolve_start_of_turn(fight)
        self.energy = 3
        self.draw(5)

    def resolve_turn(self, fight: "Fight") -> bool:
        return self.player_turn_callback(fight)

    def resolve_end_of_turn(self, fight: "Fight") -> None:
        super().resolve_end_of_turn(fight)
        
        if self.hand.cards[AscendersBane()] > 0:
            del self.hand.cards[AscendersBane()]

        self.discard_pile += self.hand
        self.hand = CardPile()

@dataclass(repr=False)
class Ironclad(Player):
    id: int = 0
    draw_pile: CardPile = field(
        default_factory=lambda: CardPile(
            cards=Counter({
                Strike(): 5,
                Defend(): 4,
                Bash(): 1,
                AscendersBane(): 1,
            })
        )
    )
