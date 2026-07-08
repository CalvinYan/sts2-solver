"""Represents a single combat in Slay the Spire 2."""

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from character.enemy import Enemy
from character.player import Player

MAX_ENEMIES = 5


@dataclass
class Fight:
    player: Player
    enemies: list[Enemy]
    turn: int = 0
    verbose: bool = False

    def __post_init__(self):
        assert len(self.enemies) in range(MAX_ENEMIES + 1)

    def loop(self) -> None:
        self.turn += 1

        if self.verbose:
            print(self)

        self.player.resolve_start_of_turn()
        while not self.player.resolve_turn(self):
            pass

        self.player.resolve_end_of_turn()

        self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]

        if self.verbose:
            print(self)

        for enemy in self.enemies:
            enemy.resolve_start_of_turn()
        for enemy in self.enemies:
            enemy.resolve_turn(self)
        for enemy in self.enemies:
            enemy.resolve_end_of_turn()

        if self.verbose:
            print(self)

    def is_over(self) -> bool:
        return all(enemy.hp <= 0 for enemy in self.enemies) or self.player.hp <= 0

    def start(self) -> None:
        while not self.is_over():
            self.loop()
        if self.verbose:
            print(f"Fight ended after {self.turn} turns. Player HP loss: {self.player.hp}")

    # Helper method for dp solve - determines the probability distribution of the player's next state.
    # For our use case, we only need to compute this distribution when the player draws cards, so the method is
    # primarily dedicated to modelling draw orders.
    # def next_states(self, ):
    # draws = list[]
    # for card in sorted(self.draw_pile).
    # pass

    # Vector representation of a Fight for interpretation by learning models.
    # The representation is entirely defined by:
    # - The vector representation of the player
    # - For n in 1..5: the vector representation of the nth enemy, or all zeroes if it doesn't exist
    # - The number of the current turn
    def to_vector(self) -> np.ndarray:
        enemies_padded = self.enemies + [None] * (MAX_ENEMIES - len(self.enemies))
        return np.concatenate(
            [
                self.player.to_vector(),
                *[Enemy.to_vector(enemy) for enemy in enemies_padded],
                [self.turn],
            ]
        )

    def __str__(self) -> str:
        return f"\nTurn {self.turn}\n\nEnemies:\n{'\n'.join(str(enemy) for enemy in self.enemies)}\n\nPlayer:\n{self.player}"
