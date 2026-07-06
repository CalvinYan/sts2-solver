from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field

import numpy as np

from util.core import Action, Move
from util.effect import Effect

@dataclass(kw_only=True, repr=False)
class Character:
    """Represents a player or enemy in the fight."""
    name: str
    id: int
    hp: int
    block: int = 0
    buffs: list[Effect] = field(default_factory=list)
    debuffs: list[Effect] = field(default_factory=list)
    verbose: bool = False

    def take_damage(self, damage: int) -> None:
        self.hp -= max(0, damage - self.block)
        self.block = max(0, self.block - damage)

    def receive_buffs(self, buffs: list[Effect]) -> None:
        for buff_incoming in buffs:
            for buff_current in self.buffs:
                if buff_current.stack(buff_incoming):
                    break
            else:
                self.buffs.append(buff_incoming)

    def receive_debuffs(self, debuffs: list[Effect]) -> None:
        for debuff_incoming in debuffs:
            for debuff_current in self.debuffs:
                if debuff_current.stack(debuff_incoming):
                    break
            else:
                self.debuffs.append(debuff_incoming)

    # Resolve all start-of-turn effects for the character.
    def resolve_start_of_turn(self, fight: "Fight") -> None:
        self.block = 0

    # Resolve the character's turn. Returns whether or not the character has ended their turn.
    def resolve_turn(self, fight: "Fight") -> bool:
        return True

    # Resolve all end-of-turn effects for the character.
    def resolve_end_of_turn(self, fight: "Fight") -> None:
        new_buffs = []
        new_debuffs = []
        for buff in self.buffs:
            if buff.duration is not None:
                buff.duration -= 1
            if buff.duration != 0:
                new_buffs.append(buff)

        self.buffs = new_buffs

        for debuff in self.debuffs:
            if debuff.duration is not None:
                debuff.duration -= 1
            if debuff.duration != 0:
                new_debuffs.append(debuff)

        self.debuffs = new_debuffs

    def act(self, target: Character, action: Action) -> None:
        if self.verbose:
            if target:
                print(f"{self.name} uses {action} on {target.name}")
            else:
                print(f"{self.name} uses {action}")

        move = Move(action=deepcopy(action), actor=self, target=target)

        for buff in self.buffs:
            buff.resolve(move, is_target=False)
        for debuff in self.debuffs:
            debuff.resolve(move, is_target=False)

        if target:
            for buff in target.buffs:
                buff.resolve(move, is_target=True)
            for debuff in target.debuffs:
                debuff.resolve(move, is_target=True)

            if move.action.damage:
                target.take_damage(move.action.damage)

            target.receive_debuffs(move.action.debuffs)

        if move.action.block:
            self.block += move.action.block

        self.receive_buffs(move.action.buffs)

    def to_vector(self) -> np.ndarray:
        if self is None:
            return np.concatenate([
                [0, 0, 0],
                Effect.effects_to_vector(list()),
                Effect.effects_to_vector(list())
            ])
        return np.concatenate([
            [self.id, self.hp, self.block],
            Effect.effects_to_vector(self.buffs),
            Effect.effects_to_vector(self.debuffs)
        ])

    def __repr__(self) -> str:
        retval = f"{self.name} ({self.block}){self.hp}"
        for buff in self.buffs:
            retval += f" ^({buff})"
        for debuff in self.debuffs:
            retval += f" v({debuff})"

        return retval
