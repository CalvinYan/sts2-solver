# type: ignore
"""Bridges the dp_viewer web form and the solver engine.

Everything that knows about the engine's object model and its `to_vector()` serialization
lives here, so `app.py` only ever deals with plain dicts and the resulting state key.

The state key produced here must match the keys stored in ``data/dp_data.csv``: a tuple of
138 ints (the `Fight.to_vector()` representation) which, combined with a trailing action id,
forms a full state-action key in the dp table.
"""

from __future__ import annotations

import os
import sys
from collections import Counter

# Allow importing the engine modules that live in the repository root.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import character.enemies  # noqa: F401  (imported for its enemy-registration side effects)
from card import ID_TO_CARD, CardPile
from character.enemy import ID_TO_ENEMY, Enemy
from character.player import ID_TO_PLAYER, Player
from fight import Fight

# The action id stored for "end your turn" rather than playing a card.
END_TURN_ACTION = -1


def player_classes() -> dict[int, str]:
    """Player ids that the engine can actually reconstruct, mapped to their class name."""
    return {pid: cls.__name__ for pid, cls in ID_TO_PLAYER.items()}


def enemy_classes() -> dict[int, str]:
    """Enemy ids the engine knows about, mapped to their class name."""
    return {eid: cls.__name__ for eid, cls in ID_TO_ENEMY.items()}


def enemy_intents(enemy_id: int) -> dict[int, str]:
    """The intent ids available for an enemy, mapped to their intent class name.

    Probes ``id_to_intent`` since each enemy defines its own intent registry. Stops at the
    first id the enemy rejects, and de-duplicates by intent id so scaffolded enemies (whose
    fallback ``id_to_intent`` returns the same generic intent for every id) collapse to one.
    """
    cls = ID_TO_ENEMY[enemy_id]
    intents: dict[int, str] = {}
    for probe_id in range(16):
        try:
            intent = cls.id_to_intent(probe_id)
        except Exception:
            break
        if intent.id in intents:
            continue
        intents[intent.id] = type(intent).__name__
    return intents


def card_ids() -> dict[int, str]:
    """Card ids that appear in the pile vectors, mapped to their class name."""
    return {cid: cls.__name__ for cid, cls in sorted(ID_TO_CARD.items())}


def _build_pile(counts: dict[int, int]) -> CardPile:
    cards: Counter = Counter()
    for card_id, count in counts.items():
        if count:
            cards[ID_TO_CARD[card_id]()] = count
    return CardPile(cards=cards)


def build_state_key(
    *,
    player_id: int,
    enemy_id: int,
    turn: int,
    player_hp: int,
    player_block: int,
    player_energy: int,
    enemy_hp: int,
    enemy_block: int,
    enemy_intent: int,
    draw: dict[int, int],
    hand: dict[int, int],
    discard: dict[int, int],
) -> tuple[int, ...]:
    """Reconstruct a Fight from form inputs and return its `to_vector()` state key.

    Reuses the engine's own serialization so the key is guaranteed to match how the solver
    wrote it. Effects on the player and enemy are not part of the form, so the reconstructed
    characters carry no effects.
    """
    if player_id not in ID_TO_PLAYER:
        raise ValueError(f"No engine support for player id {player_id}")
    if enemy_id not in ID_TO_ENEMY:
        raise ValueError(f"No engine support for enemy id {enemy_id}")

    player: Player = ID_TO_PLAYER[player_id](
        name="Player",
        hp=player_hp,
        block=player_block,
        energy=player_energy,
        draw_pile=_build_pile(draw),
        hand=_build_pile(hand),
        discard_pile=_build_pile(discard),
        player_turn_callback=None,
    )

    enemy_cls = ID_TO_ENEMY[enemy_id]
    enemy: Enemy = enemy_cls(
        name="Enemy",
        hp=enemy_hp,
        block=enemy_block,
        intent=enemy_cls.id_to_intent(enemy_intent),
    )

    fight = Fight(player=player, enemies=[enemy], turn=turn)
    return tuple(int(x) for x in fight.to_vector())


def action_label(action_id: int) -> str:
    """Human-readable label for a stored action id."""
    if action_id == END_TURN_ACTION:
        return "End turn"
    return ID_TO_CARD[action_id].__name__ if action_id in ID_TO_CARD else f"Action {action_id}"
