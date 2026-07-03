from dataclasses import dataclass

@dataclass
class Thorns(Effect):
    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target:
            move.actor.take_damage(self.power)
