from dataclasses import dataclass

@dataclass
class Weak(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target:
            move.action.damage = int(move.action.damage * 0.70)
