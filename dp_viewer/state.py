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
from fractions import Fraction

# Allow importing the engine modules that live in the repository root.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import character.enemies  # noqa: F401  (imported for its enemy-registration side effects)
from card import ID_TO_CARD, CardPile
from character.core import Character
from character.enemies import SludgeSpinner
from character.enemy import ID_TO_ENEMY, Enemy
from character.player import ID_TO_PLAYER, Player
from fight import Fight
from util.effect import ID_TO_EFFECT, Effect

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


def effect_types() -> dict[int, dict]:
    """Effect ids mapped to {name, power, duration}, where power/duration flag which stat the
    effect is parameterized by.

    The relevant stat is read from each effect subclass's own annotations (e.g. Strength
    declares ``power: int``, Vulnerable declares ``duration: int``).
    """
    result: dict[int, dict] = {}
    for eid, cls in sorted(ID_TO_EFFECT.items()):
        own = cls.__dict__.get("__annotations__", {})
        uses_power = "power" in own
        uses_duration = "duration" in own
        result[eid] = {"name": cls.__name__, "power": uses_power, "duration": uses_duration}
    return result


def _build_pile(counts: dict[int, int]) -> CardPile:
    cards: Counter = Counter()
    for card_id, count in counts.items():
        if count:
            cards[ID_TO_CARD[card_id]()] = count
    return CardPile(cards=cards)


def _build_effects(specs: dict[int, dict[str, int]]) -> list[Effect]:
    """Build effect objects from {effect_id: {"power": int, "duration": int}} specs."""
    effects: list[Effect] = []
    for eid, vals in specs.items():
        present = vals.get("present") or False
        power = vals.get("power") or None
        duration = vals.get("duration") or None
        if not present:
            continue
        effects.append(ID_TO_EFFECT[eid](id=eid, power=power, duration=duration))
    return effects


def build_fight(
    *,
    player_id: int,
    enemy_id: int,
    turn: int = 0,
    player_hp: int | None = None,
    player_block: int = 0,
    player_energy: int = 3,
    enemy_hp: int | None = None,
    enemy_block: int = 0,
    enemy_intent: int | None = None,
    draw: dict[int, int] | None = None,
    hand: dict[int, int] | None = None,
    discard: dict[int, int] | None = None,
    player_effects: dict[int, dict[str, int]] | None = None,
    enemy_effects: dict[int, dict[str, int]] | None = None,
) -> tuple[int, ...]:
    """Reconstruct a Fight from form inputs."""
    if player_id not in ID_TO_PLAYER:
        raise ValueError(f"No engine support for player id {player_id}")
    if enemy_id not in ID_TO_ENEMY:
        raise ValueError(f"No engine support for enemy id {enemy_id}")

    player: Player = ID_TO_PLAYER[player_id](
        name="Player",
        block=player_block,
        energy=player_energy,
        effects=_build_effects(player_effects or {}),
        hand=_build_pile(hand or {}),
        discard_pile=_build_pile(discard or {}),
    )

    if player_hp is not None:
        player.hp = player_hp
    if draw is not None:
        player.draw_pile = _build_pile(draw)

    enemy_cls = ID_TO_ENEMY[enemy_id]
    enemy: Enemy = enemy_cls(
        name="Enemy",
        block=enemy_block,
        effects=_build_effects(enemy_effects or {}),
    )

    if enemy_hp is not None:
        enemy.hp = enemy_hp
    if enemy_intent is not None:
        enemy.intent = enemy_cls.id_to_intent(enemy_intent)

    fight = Fight(player=player, enemies=[enemy], turn=turn or 0)
    return fight


def action_label(action_id: int) -> str:
    """Human-readable label for a stored action id."""
    if action_id == END_TURN_ACTION:
        return "End turn"
    return ID_TO_CARD[action_id].__name__ if action_id in ID_TO_CARD else f"Action {action_id}"


def describe_form(fight: Fight) -> dict:
    """Decompose a Fight back into the values of the web form's fields, so a successor state
    can be loaded into the form and re-queried."""
    player = fight.player
    enemy = fight.enemies[0]

    def effect_specs(character: Character) -> dict[int, dict[str, int]]:
        specs = {eid: {"present": False, "power": 0, "duration": 0} for eid in effect_types()}
        for effect in character.effects:
            if effect.id in specs:
                specs[effect.id] = {"present": True, "power": effect.power or 0, "duration": effect.duration or 0}
        return specs

    def pile_counts(pile: CardPile) -> dict[int, int]:
        counts = {cid: 0 for cid in ID_TO_CARD}
        for card, count in pile.cards.items():
            counts[card.id] = count
        return counts

    return {
        "player": player.id,
        "enemy": enemy.id,
        "turn": fight.turn,
        "player_hp": player.hp,
        "player_block": player.block,
        "player_energy": player.energy,
        "enemy_hp": enemy.hp,
        "enemy_block": enemy.block,
        "enemy_intent": enemy.intent.id,
        "player_effects": effect_specs(player),
        "enemy_effects": effect_specs(enemy),
        "draw": pile_counts(player.draw_pile),
        "hand": pile_counts(player.hand),
        "discard": pile_counts(player.discard_pile),
    }


def _pile_label(pile: CardPile) -> str:
    parts = [
        f"{card} ×{count}" if count > 1 else str(card)
        for card, count in sorted(pile.cards.items(), key=lambda item: item[0].id)
    ]
    return ", ".join(parts) if parts else "nothing"


def _outcome(fight: Fight, prob: Fraction, label: str) -> dict:
    return {
        "prob": prob,
        "state_key": tuple(int(x) for x in fight.to_vector()),
        "label": label,
        "form": describe_form(fight),
    }


def _turn_start_outcomes(fight: Fight, prob: Fraction = Fraction(1), label_suffix: str = "") -> list[dict]:
    """Stage the player's turn start on a fight and branch over the possible draws.

    Mirrors search_player_turn_start in fight.py: the turn advances, energy resets to 3, block
    resets, and each draw from next_states() becomes one outcome. Mutates the given fight.
    """
    fight.turn += 1
    fight.player.energy = 3
    Character.resolve_start_of_turn(fight.player)
    outcomes = []
    for draw_pile, hand, discard_pile, draw_prob in fight.player.next_states():
        fight.player.draw_pile = draw_pile
        fight.player.hand = hand
        fight.player.discard_pile = discard_pile
        outcomes.append(_outcome(fight, prob * draw_prob, f"Draw {_pile_label(hand)}" + label_suffix))
    return outcomes


def start_of_turn(fight: Fight) -> dict:
    """Resolve the start of the player's turn directly from a state, without playing an action.

    Lets the user view every possible draw from the current fight state — e.g. all opening
    hands, by staging from the pre-first-turn state (turn 0, full draw pile, empty hand).
    Returns the same shape as advance_state, plus the number of the turn being started.
    """
    if fight.is_over():
        raise ValueError("The fight is already over in this state")
    outcomes = _turn_start_outcomes(fight)
    return {"hp_lost": 0, "terminal": None, "turn": fight.turn, "outcomes": outcomes}


def advance_state(state_key: tuple[int, ...], action_id: int) -> dict:
    """Advance a state by one action, returning the distribution of successor states.

    Mirrors the sequencing of the search methods in fight.py (search_player_turn_action →
    search_player_turn_end → search_enemy_turn_start/…/_end → search_player_turn_start),
    calling the same engine methods in the same order, so successor keys match the keys the
    solver wrote into the dp table.

    Returns {"hp_lost": int, "terminal": "victory" | "defeat" | None, "outcomes": [...]}.
    A card play yields one outcome; ending the turn branches over enemy intents (SludgeSpinner)
    and the player's possible draws.
    """
    fight, _ = Fight.from_vector(tuple(state_key))
    player = fight.player
    hp_start = player.hp

    if action_id != END_TURN_ACTION:
        if action_id not in ID_TO_CARD:
            raise ValueError(f"Unknown action id {action_id}")
        card = ID_TO_CARD[action_id]()
        if player.hand.cards[card] == 0:
            raise ValueError(f"{card} is not in the player's hand")
        if not player.can_play(card):
            raise ValueError(f"Not enough energy to play {card}")

        player.play(card, fight.enemies[0])
        hp_lost = hp_start - player.hp
        if fight.is_over():
            terminal = "defeat" if player.hp <= 0 else "victory"
            return {"hp_lost": hp_lost, "terminal": terminal, "outcomes": []}
        return {
            "hp_lost": hp_lost,
            "terminal": None,
            "outcomes": [_outcome(fight, Fraction(1), f"After playing {card}")],
        }

    # End turn: player end-of-turn, then the enemies' full turn.
    player.resolve_end_of_turn()
    if fight.is_over():
        return {"hp_lost": 0, "terminal": "victory", "outcomes": []}

    for enemy in fight.enemies:
        enemy.resolve_start_of_turn()
    for enemy in fight.enemies:
        enemy.resolve_turn(fight)
    hp_lost = hp_start - player.hp
    if fight.is_over():
        return {"hp_lost": hp_lost, "terminal": "defeat", "outcomes": []}

    # Intent transition, exactly as search_enemy_turn_end branches it: a lone SludgeSpinner
    # rolls its next intent; every other enemy advances deterministically via end-of-turn.
    if len(fight.enemies) == 1 and isinstance(fight.enemies[0], SludgeSpinner):
        intent_branches = fight.enemies[0].intent.next_intents()
        branching_intents = True
    else:
        for enemy in fight.enemies:
            enemy.resolve_end_of_turn()
        intent_branches = [(None, Fraction(1))]
        branching_intents = False

    mid_vector = fight.to_vector()
    outcomes = []
    for next_intent, intent_prob in intent_branches:
        branch, _ = Fight.from_vector(mid_vector)
        if next_intent is not None:
            branch.enemies[0].intent = next_intent
        suffix = f" — intent: {next_intent}" if branching_intents else ""
        outcomes.extend(_turn_start_outcomes(branch, intent_prob, suffix))

    return {"hp_lost": hp_lost, "terminal": None, "outcomes": outcomes}
