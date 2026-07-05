from __future__ import annotations

from dataclasses import dataclass, field

@dataclass(repr=False)
class Action:
    """An atomic decision with a particular outcome."""
    damage: int = None
    block: int = None
    buffs: list["Effect"] = field(default_factory=list)
    debuffs: list["Effect"] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Action({", ".join(f"{k}={v}" for k, v in self.__dict__.items() if v)})"

    def __hash__(self):
        return hash((self.damage, self.block, tuple(self.buffs), tuple(self.debuffs)))

@dataclass
class Move:
    """An action by one character upon another (can be themselves). Used for both player card plays and enemy turns."""
    action: Action
    actor: "Character"
    target: "Character"
