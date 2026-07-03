from dataclasses import dataclass

from util.core import Effect, Move

@dataclass
class Strength(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target:
            move.action.damage += self.power

@dataclass
class Thorns(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target:
            move.actor.take_damage(self.power)

@dataclass
class Vulnerable(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target:
            move.action.damage = int(move.action.damage * 1.5)

@dataclass
class Frail(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target:
            move.action.block = int(move.action.block * 0.75)

@dataclass
class Weak(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target:
            move.action.damage = int(move.action.damage * 0.75)

@dataclass
class Shrink(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target:
            move.action.damage = int(move.action.damage * 0.70)
