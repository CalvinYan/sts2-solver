from __future__ import annotations

from dataclasses import dataclass, field

@dataclass(repr=False)
class Action:
    """An atomic decision with a particular outcome."""
    damage: int = None
    block: int = None
    buffs: list[Effect] = field(default_factory=list)
    debuffs: list[Effect] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Action({", ".join(f"{k}={v}" for k, v in self.__dict__.items() if v)})"

    def __hash__(self):
        return hash((self.damage, self.block, tuple(self.buffs), tuple(self.debuffs)))

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

    def __hash__(self):
        return hash((type(self), self.power, self.duration))

    def __repr__(self) -> str:
        retval = f"{type(self).__name__}"
        if self.power is not None:
            retval += f" {self.power}"
        if self.duration is not None:
            retval += f" {self.duration}"

        return retval

@dataclass
class Move:
    """An action by one character upon another (can be themselves). Used for both player card plays and enemy turns."""
    action: Action
    actor: "Character"
    target: "Character"
