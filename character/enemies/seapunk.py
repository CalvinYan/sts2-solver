from dataclasses import dataclass, field

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Strength


@dataclass(frozen=True)
class SeaKick(Intent):
    id: int = 0

    def actions(self) -> list[Action]:
        return [Action(damage=13)]

    def next(self) -> Intent:
        return SpinningKick()


@dataclass(frozen=True)
class SpinningKick(Intent):
    id: int = 1

    def actions(self) -> list[Action]:
        return [Action(damage=2) for _ in range(4)]

    def next(self) -> Intent:
        return BubbleBurp()


@dataclass(frozen=True)
class BubbleBurp(Intent):
    id: int = 2

    def actions(self) -> list[Action]:
        return [Action(block=8, actor_effects=[Strength(power=2)])]

    def next(self) -> Intent:
        return SeaKick()


@dataclass
class Seapunk(Enemy):
    id: int = 5
    intent: Intent = field(default_factory=SeaKick)
    min_hp: int = 47
    max_hp: int = 49

    @staticmethod
    def id_to_intent(intent_id: int) -> Intent:
        return ID_TO_INTENT[intent_id](id=intent_id)


ID_TO_INTENT: dict[int, type[Intent]] = {
    SeaKick.id: SeaKick,
    SpinningKick.id: SpinningKick,
    BubbleBurp.id: BubbleBurp,
}
