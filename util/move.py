from dataclasses import dataclass

@dataclass
class Move:
    """An action by one character upon another (can be themselves). Used for both player card plays and enemy turns."""
    action: Action
    actor: Character
    target: Character
