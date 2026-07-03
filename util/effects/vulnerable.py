from dataclasses import dataclass

@dataclass
class Vulnerable(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target:
            move.action.damage = int(move.action.damage * 1.5)
