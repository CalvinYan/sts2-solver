from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from character.core import Character
    from util.effect import Effect


@dataclass
class Action:
    """An atomic decision with a particular outcome."""

    damage: int | None = None
    block: int | None = None
    stars_gained: int = 0
    actor_effects: list[Effect] = field(default_factory=list)
    target_effects: list[Effect] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Action({", ".join(f"{k}={v}" for k, v in self.__dict__.items() if v)})"

    # Copying an Action only has to rebuild the action itself and its effects; every other field is
    # immutable. Skipping the generic dataclass copy protocol makes this considerably cheaper, and
    # Character.act copies an Action for every card played and every enemy action resolved.
    def __deepcopy__(self, memo) -> Action:
        copied = Action(
            damage=self.damage,
            block=self.block,
            stars_gained=self.stars_gained,
            actor_effects=[deepcopy(effect, memo) for effect in self.actor_effects],
            target_effects=[deepcopy(effect, memo) for effect in self.target_effects],
        )
        memo[id(self)] = copied

        return copied


@dataclass
class Move:
    """An action by one character upon another (can be themselves). Used for both player card plays and enemy turns."""

    action: Action
    actor: Character
    target: Character | None
