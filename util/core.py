from __future__ import annotations

from dataclasses import dataclass, field

@dataclass
class Action:
    """An atomic decision with a particular outcome."""
    damage: int = 0
    block: int = 0
    buffs: list[Effect] = field(default_factory=list)
    debuffs: list[Effect] = field(default_factory=list)

@dataclass
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

@dataclass
class Move:
    """An action by one character upon another (can be themselves). Used for both player card plays and enemy turns."""
    action: Action
    actor: "Character"
    target: "Character"
