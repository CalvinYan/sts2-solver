from dataclasses import dataclass

@dataclass
class Effect:
    """
    Any status effect on a character, be it a buff, debuff, or power. Contains some combination of a power (how potent
    the effect is) and duration (how many turns the effect lasts).
    """
    power: int = None
    duration: int = None

    # Resolve the effect on the given move, depending on whether or not the effect belongs to the actor or target
    def resolve(self, move: Move, is_target: bool) -> None:
        pass
