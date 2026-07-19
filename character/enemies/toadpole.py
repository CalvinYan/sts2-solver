from dataclasses import dataclass

from character.enemy import Enemy, Intent
from util.core import Action
from util.effect import Thorns


@dataclass(frozen=True)
class Spiken(Intent):
    id: int = 0

    def actions(self) -> list[Action]:
        return [Action(actor_effects=[Thorns(power=2, duration=2)])]

    def next(self) -> Intent:
        return SpikeSpit()


@dataclass(frozen=True)
class SpikeSpit(Intent):
    id: int = 1

    def actions(self) -> list[Action]:
        return [Action(damage=4), Action(damage=4), Action(damage=4)]

    def next(self) -> Intent:
        return Whirl()


@dataclass(frozen=True)
class Whirl(Intent):
    id: int = 2

    def actions(self) -> list[Action]:
        return [Action(damage=8)]

    def next(self) -> Intent:
        return Spiken()


@dataclass(kw_only=True)
class Toadpole(Enemy):
    id: int = 8
    intent: Intent
    min_hp: int = 22
    max_hp: int = 26

    @staticmethod
    def id_to_intent(intent_id: int) -> Intent:
        return ID_TO_INTENT[intent_id](id=intent_id)


ID_TO_INTENT: dict[int, type[Intent]] = {
    Spiken.id: Spiken,
    SpikeSpit.id: SpikeSpit,
    Whirl.id: Whirl,
}
