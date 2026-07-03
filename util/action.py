from dataclasses import dataclass

@dataclass
class Action:
    """An atomic decision with a particular outcome."""
    damage: int = 0
    block: int = 0
    buffs: list[Effect] = []
    debuffs: list[Effect] = []
