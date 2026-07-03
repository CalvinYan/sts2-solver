from __future__ import annotations

import random

from collections import Counter
from dataclasses import dataclass, field
from typing import Callable

from card import AscendersBane, Bash, Card, Defend, Strike
from character.core import Character

@dataclass(kw_only=True)
class Player(Character):
    """
    A player-controlled character with the cards in their deck distributed between their hand, draw pile, and discard pile.
    Each fight has exactly one player.
    """
    # We don't care about the player's HP, only how much they lose during the fight
    hp: int = 0
    energy: int = 3
    hand: Counter[Card] = field(default_factory=Counter)
    draw_pile: Counter[Card]
    discard_pile: Counter[Card] = field(default_factory=Counter)

    player_turn_callback: Callable[["Fight"], bool]

    def draw(self, cards: int) -> None:
        for _ in range(cards):
            if self.hand.total >= 10:
                print("Hand is full")
                return

            if not self.draw_pile:
                self.draw_pile = self.discard_pile
                self.discard_pile = Counter()

            try:
                card = random.choice(list(self.draw_pile.elements()))
            except IndexError:
                print("No cards left to draw")
                return

            self.draw_pile[card] -= 1
            if self.draw_pile[card] == 0:
                del self.draw_pile[card]

            self.hand[card] += 1

    def play(self, card: Card, target: Character = None) -> None:
        if self.hand[card] == 0:
            print("Card not in hand")
            return

        self.act(target=target, action=card.action)

        self.energy -= card.cost

        self.hand[card] -= 1
        if self.hand[card] == 0:
            del self.hand[card]

        self.discard_pile[card] += 1

    def resolve_start_of_turn(self) -> None:
        super().resolve_start_of_turn()
        self.energy = 3
        self.draw(5)

    def resolve_turn(self, fight: "Fight") -> bool:
        return self.player_turn_callback(fight)

    def resolve_end_of_turn(self, fight: "Fight") -> None:
        super().resolve_end_of_turn(fight)
        self.discard_pile += self.hand
        self.hand = Counter()

@dataclass
class Ironclad(Player):
    draw_pile: Counter[Card] = field(default_factory=lambda: Counter({
        Strike(): 5,
        Defend(): 5,
        Bash(): 1,
        AscendersBane(): 1,
    }))
