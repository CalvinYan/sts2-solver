from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from util.core import Move


@dataclass(kw_only=True)
class Effect:
    """
    Any status effect on a character, be it a buff, debuff, or power. Contains some combination of a power (how potent
    the effect is) and duration (how many turns the effect lasts).
    """

    id: int
    power: int | None = None
    duration: int | None = None

    # Resolve the effect on the given move, depending on whether or not the effect belongs to the actor or target
    def resolve(self, move: Move, is_target: bool) -> None:
        pass

    # Stack this effect with another one of the same class
    def stack(self, other: Effect) -> bool:
        if type(self) is not type(other):
            return False
        if self.power is not None and other.power is not None:
            self.power += other.power
        if self.duration is not None and other.duration is not None:
            self.duration += other.duration

        return True

    def to_vector(self: Effect) -> np.ndarray:
        # This positional encoding ensures that the vector of a list of effects is equal to the sum of the vectors of each effect
        arr = np.zeros((max(ID_TO_EFFECT.keys()) + 1, 2), dtype=int)
        arr[self.id] = (
            self.power if self.power is not None else 0,
            self.duration if self.duration is not None else 0,
        )

        return arr.flatten()

    def __hash__(self) -> int:
        return hash((self.id, self.power, self.duration))

    def __str__(self) -> str:
        retval = f"{type(self).__name__}"
        if self.power is not None:
            retval += f" {self.power}"
        if self.duration is not None:
            retval += f" {self.duration}"

        return retval

    @staticmethod
    def effects_to_vector(effects: list[Effect]) -> np.ndarray:
        return sum((effect.to_vector() for effect in effects), start=Effect(id=0).to_vector())


@dataclass(eq=False, kw_only=True)
class Strength(Effect):
    power: int
    id: int = 0

    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage += self.power


@dataclass(eq=False, kw_only=True)
class Thorns(Effect):
    power: int
    id: int = 1

    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target and move.action.damage is not None:
            move.actor.take_damage(self.power)


@dataclass(eq=False, kw_only=True)
class Vulnerable(Effect):
    duration: int
    id: int = 2

    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 1.5)


@dataclass(eq=False, kw_only=True)
class Weak(Effect):
    duration: int
    id: int = 3

    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 0.75)


@dataclass(eq=False, kw_only=True)
class Frail(Effect):
    duration: int
    id: int = 4

    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.block is not None:
            move.action.block = int(move.action.block * 0.75)


@dataclass(eq=False, kw_only=True)
class Shrink(Effect):
    id: int = 5

    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 0.70)


ID_TO_EFFECT: dict[int, type[Effect]] = {
    Strength.id: Strength,
    Thorns.id: Thorns,
    Vulnerable.id: Vulnerable,
    Weak.id: Weak,
    Frail.id: Frail,
    Shrink.id: Shrink,
}
