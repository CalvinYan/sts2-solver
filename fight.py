"""Represents a single combat in Slay the Spire 2."""
from dataclasses import dataclass

from character.enemy import Enemy
from character.player import Player

@dataclass(repr=False)
class Fight:
    player: Player
    enemies: list[Enemy]
    turn: int = 0
    verbose: bool = False

    def loop(self) -> None:
        self.turn += 1

        if self.verbose:
            print(self)

        self.player.resolve_start_of_turn(self)
        while not self.player.resolve_turn(self):
            pass

        self.player.resolve_end_of_turn(self)

        self.enemies = [enemy for enemy in self.enemies if enemy.hp > 0]

        if self.verbose:
            print(self)

        for enemy in self.enemies:
            enemy.resolve_start_of_turn(self)
        for enemy in self.enemies:
            enemy.resolve_turn(self)
        for enemy in self.enemies:
            enemy.resolve_end_of_turn(self)

        if self.verbose:
            print(self)

    def is_over(self) -> bool:
        return all(enemy.hp <= 0 for enemy in self.enemies) or self.turn >= 20

    def start(self) -> None:
        while not self.is_over():
            self.loop()
        print(f"Fight ended after {self.turn} turns. Player HP loss: {self.player.hp}")

    def __repr__(self) -> str:
        return f"\nTurn {self.turn}\nPlayer: {self.player}\nEnemies: {'\n'.join(repr(enemy) for enemy in self.enemies)}\n"
