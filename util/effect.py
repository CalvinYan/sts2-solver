from dataclasses import dataclass

from util.core import Move

@dataclass(repr=False)
class Effect:
    """
    Any status effect on a character, be it a buff, debuff, or power. Contains some combination of a power (how potent
    the effect is) and duration (how many turns the effect lasts).
    """
    id: int
    power: int = None
    duration: int = None

    # Resolve the effect on the given move, depending on whether or not the effect belongs to the actor or target
    def resolve(self, move: Move, is_target: bool) -> None:
        pass

    # Stack this effect with another one of the same class
    def stack(self, other: Effect) -> bool:
        if type(self) != type(other): return False
        if self.power is not None and other.power is not None:
            self.power += other.power
        if self.duration is not None and other.duration is not None:
            self.duration += other.duration

        return True

    def to_vector(self) -> tuple:
        # This positional encoding ensures that the vector of a list of effects is equal to the sum of the vectors of each effect
        lst = [(0, 0, 0)] * (max(ID_TO_EFFECT.keys()) + 1)
        lst[self.id] = (1, self.power if self.power is not None else 0, self.duration if self.duration is not None else 0)
        
        return sum(lst, ())

    def __hash__(self) -> int:
        return hash((self.id, self.power, self.duration))

    def __repr__(self) -> str:
        retval = f"{type(self).__name__}"
        if self.power is not None:
            retval += f" {self.power}"
        if self.duration is not None:
            retval += f" {self.duration}"

        return retval

    def effects_to_vector(effects: list[Effect]) -> tuple:
        zeroes = (0,) * 3 * (max(ID_TO_EFFECT.keys()) + 1)
        return tuple(map(sum, zip(zeroes, *[effect.to_vector() for effect in effects])))

@dataclass(repr=False, eq=False)
class Strength(Effect):
    id: int = 0
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage += self.power

@dataclass(repr=False, eq=False)
class Thorns(Effect):
    id: int = 1
    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target and move.action.damage is not None:
            move.actor.take_damage(self.power)

@dataclass(repr=False, eq=False)
class Vulnerable(Effect):
    id: int = 2
    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 1.5)

@dataclass(repr=False, eq=False)
class Weak(Effect):
    id: int = 3
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 0.75)

@dataclass(repr=False, eq=False)
class Frail(Effect):
    id: int = 4
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.block is not None:
            move.action.block = int(move.action.block * 0.75)

@dataclass(repr=False, eq=False)
class Shrink(Effect):
    id: int = 5
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 0.70)

ID_TO_EFFECT = {
    Strength.id: Strength,
    Thorns.id: Thorns,
    Vulnerable.id: Vulnerable,
    Weak.id: Weak,
    Frail.id: Frail,
    Shrink.id: Shrink,
}
