from dataclasses import dataclass

from util.core import Move

@dataclass(repr=False)
class Effect:
    """
    Any status effect on a character, be it a buff, debuff, or power. Contains some combination of a power (how potent
    the effect is) and duration (how many turns the effect lasts).
    """
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

    def id(self) -> int:
        return EFFECT_TO_ID[type[self]]

    def to_vector(self) -> tuple:
        # This positional encoding ensures that the vector of a list of effects is equal to the sum of the vectors of each effect
        lst = [tuple(0, 0, 0)] * len(EFFECT_TO_ID)
        lst[self.id()] = (1, self.power if self.power is not None else 0, self.duration if self.duration is not None else 0)
        
        return sum(lst, ())

    def __hash__(self) -> int:
        return hash((self.id(), self.power, self.duration))

    def __repr__(self) -> str:
        retval = f"{type(self).__name__}"
        if self.power is not None:
            retval += f" {self.power}"
        if self.duration is not None:
            retval += f" {self.duration}"

        return retval

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

class Weak(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 0.75)

class Frail(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.block is not None:
            move.action.block = int(move.action.block * 0.75)

class Shrink(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target and move.action.damage is not None:
            move.action.damage = int(move.action.damage * 0.70)

EFFECT_TO_ID = {
    Strength: 0,
    Thorns: 1,
    Vulnerable: 2,
    Weak: 3,
    Frail: 4,
    Shrink: 5
}

ID_TO_EFFECT = {v: k for k, v in EFFECT_TO_ID.items()}