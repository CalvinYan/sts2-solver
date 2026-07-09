"""Represents a single combat in Slay the Spire 2."""

from __future__ import annotations

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

    # SEARCH METHODS
    #
    # The following methods are similar to loop() in that they simulate a specific phase of the fight, but instead of
    # transitioning to the next game state at random, search traverses all possible next states, and computes the
    # probability distribution of player hp losses from that point dynamic programming.
    #
    # Each search method takes in the following fields:
    # dp_table: The dynamic programming lookup table containing already computed search results
    # prob: The probability of reaching the current state from the state where search began
    def search_player_turn_start(self, dp_table: defaultdict, prob: Fraction) -> None:
        pass

    def search_player_turn(self, dp_table: defaultdict, prob: Fraction) -> None:
        pass

    def search_player_turn_end(self, dp_table: defaultdict, prob: Fraction) -> None:
        pass

    def search_enemy_turn_start(self, dp_table: defaultdict, prob: Fraction) -> None:
        pass

    def search_enemy_turn(self, dp_table: defaultdict, prob: Fraction) -> None:
        pass

    def search_enemy_turn_end(self, dp_table: defaultdict, prob: Fraction) -> None:
        pass

    def is_over(self) -> bool:
        return all(enemy.hp <= 0 for enemy in self.enemies) or self.player.hp <= 0

    def start(self) -> None:
        while not self.is_over():
            self.loop()
        if self.verbose:
            print(f"Fight ended after {self.turn} turns. Player HP loss: {self.player.hp}")

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

    @staticmethod
    def from_vector(vector: tuple) -> tuple[Fight, int]:
        indices_read = 0
        try:
            player, read = Player.from_vector(vector)
        except ValueError as e:
            raise ValueError("Error reading Player from Fight vector:", e)
        indices_read += read
        enemies = []

        for _ in range(MAX_ENEMIES):
            exists = vector[indices_read]
            if exists:
                enemy, read = Enemy.from_vector(vector[indices_read:])
                enemies.append(enemy)
            elif not enemies:
                raise ValueError("Fight vector must contain at least one Enemy")
            indices_read += read

        if len(vector) < indices_read + 1:
            raise ValueError(
                f"Not enough values in Fight vector to read turn number: expected {indices_read + 1}, got {indices_read}"
            )
        turn: int = vector[indices_read]

        return Fight(player=player, enemies=enemies, turn=turn), indices_read + 1

    def __str__(self) -> str:
        return f"\nTurn {self.turn}\n\nEnemies:\n{'\n'.join(str(enemy) for enemy in self.enemies)}\n\nPlayer:\n{self.player}"
