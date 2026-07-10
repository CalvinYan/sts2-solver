"""Represents a single combat in Slay the Spire 2."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction

import numpy as np

from card import Card
from character.core import Character
from character.enemies import SludgeSpinner
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

        # TODO: use filter here and anywhere else
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
    # transitioning to the next game state at random, search traverses all possible next states, computing the
    # probability distributions of player hp losses from each state, and returning the distributions with the best
    # expected value. State-action pairs are memoized according to dynamic programming.
    def search_player_turn_start(self, dp_table: dict[tuple, dict[int, Fraction]]) -> dict[int, Fraction]:
        self.turn += 1
        self.player.energy = 3
        Character.resolve_start_of_turn(self.player)
        results: dict[int, Fraction] = defaultdict(Fraction)
        for next_player, prob_next_player in self.player.next_states():
            next_fight = deepcopy(self)
            next_fight.player = next_player

            for hp_loss, prob_hp_loss in next_fight.search_player_turn(dp_table).items():
                results[hp_loss] += prob_hp_loss * prob_next_player

        return results

    def search_player_turn(self, dp_table: dict[tuple, dict[int, Fraction]]) -> dict[int, Fraction]:
        if self.is_over():
            return {0: Fraction(1, 1)}

        # Try playing each playable card in your hand
        results_per_action = [
            deepcopy(self).search_player_turn_action(dp_table, card)
            for card in self.player.hand.cards.keys()
            if card.playable(self.player.energy)
        ]

        # Try just ending your turn
        # In theory we don't need to deepcopy the fight here, since this path is the last one to be traversed
        results_per_action.append(self.search_player_turn_action(dp_table, None))

        # Return the probability distribution with the least expected HP loss
        return min(results_per_action, key=lambda outcomes: sum([k * v for k, v in outcomes.items()]))

    # Search after the player has committed to a specific action.
    # The action is the card to be played, or None if the player is ending their turn.
    def search_player_turn_action(self, dp_table: dict[tuple, dict[int, Fraction]], action: Card | None):
        action_id = action.id if action else -1
        state_action_pair = (*tuple(map(int, self.to_vector())), action_id)
        if state_action_pair not in dp_table:
            if action is None:
                # No deepcopy here for the same reason as above
                hp_losses = self.search_player_turn_end(dp_table)
            else:
                new_fight = deepcopy(self)
                hp_before = new_fight.player.hp
                new_fight.player.play(action, new_fight.enemies[0])
                hp_after = new_fight.player.hp
                hp_losses = {
                    hp_loss + hp_before - hp_after: prob
                    for hp_loss, prob in new_fight.search_player_turn(dp_table).items()
                }

            dp_table[state_action_pair] = hp_losses

        return dp_table[state_action_pair]

    def search_player_turn_end(self, dp_table: dict[tuple, dict[int, Fraction]]) -> dict[int, Fraction]:
        self.player.resolve_end_of_turn()
        self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]
        return self.search_enemy_turn_start(dp_table)

    def search_enemy_turn_start(self, dp_table: dict[tuple, dict[int, Fraction]]) -> dict[int, Fraction]:
        if self.is_over():
            return {0: Fraction(1, 1)}

        for enemy in self.enemies:
            enemy.resolve_start_of_turn()

        return self.search_enemy_turn(dp_table)

    def search_enemy_turn(self, dp_table: dict[tuple, dict[int, Fraction]]) -> dict[int, Fraction]:
        hp_before = self.player.hp
        for enemy in self.enemies:
            enemy.resolve_turn(self)
        hp_after = self.player.hp

        return {hp_loss + hp_before - hp_after: prob for hp_loss, prob in self.search_enemy_turn_end(dp_table).items()}

    def search_enemy_turn_end(self, dp_table: dict[tuple, dict[int, Fraction]]) -> dict[int, Fraction]:
        if self.is_over():
            return {0: Fraction(1, 1)}

        # TODO: Eventually I will have to deal with multiple enemies with random intents but
        # don't feel like doing it right now
        if len(self.enemies) == 1 and isinstance(self.enemies[0], SludgeSpinner):
            results: dict[int, Fraction] = defaultdict(Fraction)
            for next_enemy, prob_next_enemy in self.enemies[0].next_states():
                next_fight = deepcopy(self)
                next_fight.enemies = [next_enemy]

                for hp_loss, prob_hp_loss in next_fight.search_player_turn_start(dp_table).items():
                    results[hp_loss] += prob_next_enemy * prob_hp_loss
            return results
        else:
            for enemy in self.enemies:
                enemy.resolve_end_of_turn()
            return self.search_player_turn_start(dp_table)

    def is_over(self) -> bool:
        # TODO: Check only if len(self.enemies) is 0
        return all(enemy.hp <= 0 for enemy in self.enemies) or self.player.hp <= 0

    def start(self) -> None:
        while not self.is_over():
            self.loop()
        if self.verbose:
            print(f"Fight ended after {self.turn} turns. Player HP remaining: {self.player.hp}")

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
