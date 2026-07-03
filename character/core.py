from __future__ import annotations

from dataclasses import dataclass, field

from util.core import Action, Effect, Move

@dataclass(kw_only=True)
class Character:
    """Represents a player or enemy in the fight."""
    name: str
    hp: int
    block: int = 0
    buffs: list[Effect] = field(default_factory=list)
    debuffs: list[Effect] = field(default_factory=list)

    def take_damage(self, damage: int) -> None:
        self.hp -= max(0, damage - self.block)

    def receive_buffs(self, buffs: list[Effect]) -> None:
        for buff_incoming in buffs:
            for buff_current in self.buffs:
                if buff_current.stack(buff_incoming):
                    return
            self.buffs.append(buff_incoming)

    def receive_debuffs(self, debuffs: list[Effect]) -> None:
        for debuff_incoming in debuffs:
            for debuff_current in self.debuffs:
                if debuff_current.stack(debuff_incoming):
                    return
            self.debuffs.append(debuff_incoming)

    # Resolve all start-of-turn effects for the character.
    def resolve_start_of_turn(self, fight: "Fight") -> None:
        pass

    # Resolve the character's turn. Returns whether or not the character has ended their turn.
    def resolve_turn(self, fight: "Fight") -> bool:
        return True

    # Resolve all end-of-turn effects for the character.
    def resolve_end_of_turn(self, fight: "Fight") -> None:
        self.block = 0

        new_buffs = []
        new_debuffs = []
        for buff in self.buffs:
            if buff.duration is not None:
                buff.duration -= 1
            if buff.duration != 0:
                new_buffs.append(buff)

        for debuff in self.debuffs:
            if debuff.duration is not None:
                debuff.duration -= 1
            if debuff.duration != 0:
                new_debuffs.append(debuff)

    def act(self, target: Character, action: Action) -> None:
        print(f"{self.name} uses {action} on {target.name}")
        move = Move(action=action, actor=self, target=target)

        for buff in self.buffs:
            buff.resolve(move, is_target=False)
        for debuff in target.debuffs:
            debuff.resolve(move, is_target=True)

        target.take_damage(move.action.damage)
        self.block += move.action.block
        self.receive_buffs(move.action.buffs)
        target.receive_debuffs(move.action.debuffs)
