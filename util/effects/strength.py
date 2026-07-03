from dataclasses import dataclass

@dataclass
class Strength(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target:
            move.action.damage += self.power
