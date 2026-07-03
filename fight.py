"""Represents a single combat in Slay the Spire 2."""
from dataclasses import dataclass
from typing import Callable

from character.enemy import Enemy
from character.player import Player

@dataclass
class Fight:
    player: Player
    enemies: list[Enemy]
    turn: int = 0

    def loop(self) -> None:
        self.turn += 1

        self.player.resolve_start_of_turn(self)
        while not self.player.resolve_turn(self):
            pass
        self.player.resolve_end_of_turn(self)

        self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]

        for enemy in self.enemies:
            enemy.resolve_start_of_turn(self)
        for enemy in self.enemies:
            enemy.resolve_turn(self)
        for enemy in self.enemies:
            enemy.resolve_end_of_turn(self)

    def is_over(self) -> bool:
        return all(enemy.hp <= 0 for enemy in self.enemies) or self.turn >= 20

    def __str__(self) -> str:
        return f"Turn {self.turn}\nPlayer: {self.player}\nEnemies: {self.enemies}\nHP lost: {self.player.hp}"
