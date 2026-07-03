from dataclasses import dataclass, field
from random import randint

@dataclass
class Enemy(Character):
    """
    A hostile non-player character with an intent and a range of possible hp values.
    Each fight starts with one or more enemies, and ends if none remain with more than 0 HP.
    """
    hp = field(init=False)

    intent: Intent
    min_hp: ClassVar[int]
    max_hp: ClassVar[int]

    def __post_init__(self):
        self.hp = randint(self.min_hp, self.max_hp)

    def resolve_end_of_turn(self) -> None:
        super().resolve_end_of_turn(self)
        self.intent = self.intent.next()