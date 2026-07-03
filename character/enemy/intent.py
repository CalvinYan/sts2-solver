from dataclasses import dataclass

@dataclass
class Intent:
    """A sequence of actions that an enemy will perform on a given turn, with a random variable determining its next intent."""
    actions: list[Action]

    def next_intent(self) -> Intent:
        pass
