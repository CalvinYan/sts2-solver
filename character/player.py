import random

from collections import Counter
from dataclasses import dataclass
from typing import Callable

from card import Card
from character.core import Character
from fight import Fight

@dataclass
class Player(Character):
    """
    A player-controlled character with the cards in their deck distributed between their hand, draw pile, and discard pile.
    Each fight has exactly one player.
    """
    # We don't care about the player's HP, only how much they lose during the fight
    hp = 0
    energy = 3
    hand: Counter[Card] = Counter()
    draw_pile: Counter[Card]
    discard_pile: Counter[Card] = Counter()

    player_turn_callback: Callable[[Fight], None]

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

    def resolve_turn(self) -> None:
        self.player_turn_callback(self)

    def resolve_end_of_turn(self) -> None:
        super().resolve_end_of_turn()
        self.discard_pile += self.hand
        self.hand = Counter()