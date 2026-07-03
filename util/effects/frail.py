from dataclasses import dataclass

@dataclass
class Frail(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if not is_target:
            move.action.block = int(move.action.block * 0.75)
