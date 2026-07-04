from dataclasses import dataclass

from util.core import Effect, Move

class Strength(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage += self.power

class Thorns(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target and move.action.damage is not None:
            move.actor.take_damage(self.power)

class Vulnerable(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 1.5)

class Frail(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.block is not None:
            move.action.block = int(move.action.block * 0.75)

class Weak(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 0.75)

class Shrink(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 0.70)
