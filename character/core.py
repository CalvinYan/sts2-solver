"""Shared logic for all characters."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from util.core import Action, Move
from util.effect import Effect

if TYPE_CHECKING:
    from fight import Fight


@dataclass(kw_only=True)
class Character:
    """Represents a player or enemy in the fight."""

    name: str
    id: int
    hp: int
    block: int = 0
    effects: list[Effect] = field(default_factory=list)
    verbose: bool = False

    def take_damage(self, damage: int) -> None:
        self.hp -= max(0, damage - self.block)
        self.block = max(0, self.block - damage)

    def receive_effects(self, effects: list[Effect]) -> None:
        for effect_incoming in effects:
            for effect_current in self.effects:
                if effect_current.stack(effect_incoming):
                    break
            else:
                self.effects.append(effect_incoming)

    # Resolve all start-of-turn effects for the character.
    def resolve_start_of_turn(self) -> None:
        self.block = 0

    # Resolve the character's turn. Returns whether or not the character has ended their turn.
    def resolve_turn(self, fight: Fight) -> bool:
        return True

    # Resolve all end-of-turn effects for the character.
    def resolve_end_of_turn(self) -> None:
        new_effects = []
        for effect in self.effects:
            if effect.duration is not None:
                effect.duration -= 1
            if effect.duration != 0:
                new_effects.append(effect)

        self.effects = new_effects

    def act(self, target: Character | None, action: Action) -> None:
        if self.verbose:
            if target:
                print(f"{self.name} uses {action} on {target.name}")
            else:
                print(f"{self.name} uses {action}")

        move = Move(action=deepcopy(action), actor=self, target=target)

        for effect in self.effects:
            effect.resolve(move, is_target=False)

        if target:
            for effect in target.effects:
                effect.resolve(move, is_target=True)

            if move.action.damage:
                target.take_damage(move.action.damage)

            target.receive_effects(move.action.target_effects)

        if move.action.block:
            self.block += move.action.block

        self.receive_effects(move.action.actor_effects)

    def to_vector(self: Character | None) -> list[int]:
        if self is None:
            return [0, 0, 0, *Effect.effects_to_vector(list())]
        return [self.id, self.hp, self.block, *Effect.effects_to_vector(self.effects)]

    @staticmethod
    def from_vector(vector: tuple[int, ...]) -> tuple[Character, int]:
        if len(vector) < 3:
            raise ValueError(
                f"Not enough values in Character vector to read id, hp, block: expected 3, got {len(vector)}"
            )
        id, hp, block = vector[:3]

        try:
            effects, read = Effect.effects_from_vector(vector[3:])
        except ValueError as e:
            raise ValueError("Error reading Effects from Character vector:", e)

        return Character(name="Character", id=id, hp=hp, block=block, effects=effects), read + 3

    def __str__(self) -> str:
        retval = f"{self.name} ({self.block}){self.hp}"
        for effect in self.effects:
            retval += f" ({effect})"

        return retval
