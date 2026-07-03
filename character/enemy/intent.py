from dataclasses import dataclass

@dataclass
class Intent:
    """An action that an enemy will perform on a given turn, with a random variable determining its next intent."""
    action: Action

    def next_intent(self) -> Intent:
        pass
