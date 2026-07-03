from dataclasses import dataclass

@dataclass
class Move:
    """A sequence of actions by one character upon another (can be themselves). Used for both player card plays and enemy turns."""
    actions: list[Action]
    actor: Character
    target: Character
