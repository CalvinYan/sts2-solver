from dataclasses import dataclass

@dataclass
class Thorns(Effect):
    # Doesn't handle multihits properly but that's fine for starter decks
    def resolve(self, move: Move, is_target: bool) -> None:
        if is_target:
            move.actor.take_damage(self.power)
