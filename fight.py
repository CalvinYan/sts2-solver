"""Represents a single combat in Slay the Spire 2."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction

from card import Card, Defend
from character.core import Character
from character.enemies import SludgeSpinner
from character.enemy import Enemy
from character.player import Player
from util.core import Move

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
    #
    # Each search method returns the following:
    # The probability distribution of possible HP losses from the current state
    # Whether or not the search was complete (not truncated by hp_limit)

    def search_player_turn_start(
        self, dp_table: dict[tuple, dict[int, Fraction]], hp_limit: int = 0
    ) -> tuple[dict[int, Fraction], bool]:
        if self.player.hp <= hp_limit:
            return {0: Fraction(1)}, False

        player_snapshot = self.player.to_vector()
        turn_snapshot = self.turn

        search_complete = True
        self.turn += 1
        self.player.energy = 3
        Character.resolve_start_of_turn(self.player)
        results: dict[int, Fraction] = defaultdict(Fraction)
        for draw_pile_next, hand_next, discard_pile_next, prob_next_player in self.player.next_states():
            self.player.draw_pile = draw_pile_next
            self.player.hand = hand_next
            self.player.discard_pile = discard_pile_next
            hp_losses, subsearch_complete = self.search_player_turn(dp_table, hp_limit)
            for hp_loss, prob_hp_loss in hp_losses.items():
                results[hp_loss] += prob_hp_loss * prob_next_player
            if not subsearch_complete:
                search_complete = False

        self.turn = turn_snapshot
        self.player.read_vector(player_snapshot)

        return results, search_complete

    def search_player_turn(
        self, dp_table: dict[tuple, dict[int, Fraction]], hp_limit: int = 0
    ) -> tuple[dict[int, Fraction], bool]:

        def incoming_damage() -> int:
            dmg = 0
            for enemy in self.enemies:
                for action in enemy.intent.actions():
                    if action.damage:
                        move = Move(action, actor=enemy, target=self.player)
                        for effect in enemy.effects:
                            effect.resolve(move, is_target=False)
                        for effect in self.player.effects:
                            effect.resolve(move, is_target=True)
                        dmg += action.damage  # type: ignore
            return dmg

        if self.is_over():
            return {0: Fraction(1)}, True

        best_distribution = {}
        best_value = Fraction(1 << 32)
        search_complete = True

        # Try playing each playable card in your hand
        for card in list(self.player.hand.cards.keys()):
            # Optimization: Don't play defends if enemies are not attacking
            if self.player.can_play(card) and not (isinstance(card, Defend) and incoming_damage() <= self.player.block):
                hp_losses, subsearch_complete = self.search_player_turn_action(dp_table, card, hp_limit)
                if hp_losses:
                    expected_value = sum(
                        (hp_loss * prob_hp_loss for hp_loss, prob_hp_loss in hp_losses.items()), start=Fraction(0)
                    )
                    if expected_value < best_value:
                        best_distribution = hp_losses
                        best_value = expected_value
                        search_complete = subsearch_complete

                    # Optimization; terminate if lethal is found
                    if hp_losses == {0: Fraction(1)}:
                        break
        else:
            # Try just ending your turn
            hp_losses, subsearch_complete = self.search_player_turn_action(dp_table, None, hp_limit)
            if hp_losses:
                expected_value = sum(
                    (hp_loss * prob_hp_loss for hp_loss, prob_hp_loss in hp_losses.items()), start=Fraction(0)
                )
                if expected_value < best_value:
                    best_distribution = hp_losses
                    best_value = expected_value
                    search_complete = subsearch_complete

        # Return the probability distribution with the least expected HP loss
        return best_distribution, search_complete

    # Search after the player has committed to a specific action.
    # The action is the card to be played, or None if the player is ending their turn.
    def search_player_turn_action(
        self, dp_table: dict[tuple, dict[int, Fraction]], action: Card | None, hp_limit: int = 0
    ) -> tuple[dict[int, Fraction], bool]:
        action_id = action.id if action else -1
        state_action_pair = (*tuple(self.to_vector()), action_id)
        hp_losses = {}
        search_complete = True
        if state_action_pair in dp_table:
            hp_losses = dp_table[state_action_pair]
        else:
            if action is None:
                hp_losses, subsearch_complete = self.search_player_turn_end(dp_table, hp_limit)
                if not subsearch_complete:
                    search_complete = False
            else:
                player_snapshot = self.player.to_vector()
                enemy_snapshot = self.enemies[0].to_vector()
                hp_before = self.player.hp

                self.player.play(action, self.enemies[0])

                hp_after = self.player.hp
                hp_losses, subsearch_complete = self.search_player_turn(dp_table, hp_limit)
                hp_losses = {hp_loss + hp_before - hp_after: prob for hp_loss, prob in hp_losses.items()}
                if not subsearch_complete:
                    search_complete = False

                self.player.read_vector(player_snapshot)
                self.enemies[0].read_vector(enemy_snapshot)

            if search_complete:
                dp_table[state_action_pair] = hp_losses

        return hp_losses, search_complete

    def search_player_turn_end(
        self, dp_table: dict[tuple, dict[int, Fraction]], hp_limit: int = 0
    ) -> tuple[dict[int, Fraction], bool]:
        player_snapshot = self.player.to_vector()
        self.player.resolve_end_of_turn()
        result = self.search_enemy_turn_start(dp_table, hp_limit)
        self.player.read_vector(player_snapshot)
        return result

    def search_enemy_turn_start(
        self, dp_table: dict[tuple, dict[int, Fraction]], hp_limit: int = 0
    ) -> tuple[dict[int, Fraction], bool]:
        if self.is_over():
            return {0: Fraction(1)}, True

        # Covers both the block reset below and anything the enemies gain while acting in
        # search_enemy_turn (search_enemy_turn_end restores its own mutations separately)
        enemy_snapshots = [enemy.to_vector() for enemy in self.enemies]
        for enemy in self.enemies:
            enemy.resolve_start_of_turn()

        result = self.search_enemy_turn(dp_table, hp_limit)

        for enemy, snapshot in zip(self.enemies, enemy_snapshots):
            enemy.read_vector(snapshot)
        return result

    def search_enemy_turn(
        self, dp_table: dict[tuple, dict[int, Fraction]], hp_limit: int = 0
    ) -> tuple[dict[int, Fraction], bool]:
        hp_before = self.player.hp
        for enemy in self.enemies:
            enemy.resolve_turn(self)
        hp_after = self.player.hp

        hp_losses, subsearch_complete = self.search_enemy_turn_end(dp_table, hp_limit)
        hp_losses = {hp_loss + hp_before - hp_after: prob for hp_loss, prob in hp_losses.items()}
        return hp_losses, subsearch_complete

    def search_enemy_turn_end(
        self, dp_table: dict[tuple, dict[int, Fraction]], hp_limit: int = 0
    ) -> tuple[dict[int, Fraction], bool]:
        if self.is_over():
            return {0: Fraction(1)}, True

        search_complete = True
        # TODO: Eventually I will have to deal with multiple enemies with random intents but
        # don't feel like doing it right now
        if len(self.enemies) == 1 and isinstance(self.enemies[0], SludgeSpinner):
            results: dict[int, Fraction] = defaultdict(Fraction)
            current_intent = self.enemies[0].intent

            for next_intent, prob_next_intent in self.enemies[0].intent.next_intents():
                self.enemies[0].intent = next_intent
                hp_losses, subsearch_complete = self.search_player_turn_start(dp_table, hp_limit)
                for hp_loss, prob_hp_loss in hp_losses.items():
                    results[hp_loss] += prob_next_intent * prob_hp_loss
                if not subsearch_complete:
                    search_complete = False
                self.enemies[0].intent = current_intent

            return results, search_complete
        else:
            enemy_snapshots = [enemy.to_vector() for enemy in self.enemies]
            for enemy in self.enemies:
                enemy.resolve_end_of_turn()
            result = self.search_player_turn_start(dp_table, hp_limit)
            for enemy, snapshot in zip(self.enemies, enemy_snapshots):
                enemy.read_vector(snapshot)
            return result

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
    def to_vector(self) -> list[int]:
        enemies_padded = self.enemies + [None] * (MAX_ENEMIES - len(self.enemies))
        return [*self.player.to_vector(), *[i for enemy in enemies_padded for i in Enemy.to_vector(enemy)], self.turn]

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
