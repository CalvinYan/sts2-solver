# type: ignore
"""Bridges the dp_viewer web form and the solver engine.

Everything that knows about the engine's object model and its `to_vector()` serialization
lives here, so `app.py` only ever deals with plain dicts and the resulting state key.

The state key produced here must match the keys stored in ``data/dp_data.csv``: a tuple of
ints (the `Fight.to_vector()` representation) which, combined with an action tuple —
``(action_id,)`` for untargeted actions, ``(action_id, target_index)`` for targeted ones —
forms a full state-action key in the dp table.

Fights are described in terms of the encounters in ``character/encounters.py``. Each enemy
occupies a fixed "slot" (its index within the encounter); dead enemies leave the fight and the
state vector, but their slots persist in the web form with hp 0, so an ``alive_slots`` list
maps the enemies encoded in a state back to their encounter slots.
"""

from __future__ import annotations

import inspect
import os
import sys
from collections import Counter
from fractions import Fraction
from itertools import product

# Allow importing the engine modules that live in the repository root.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import character.enemies  # noqa: F401  (imported for its enemy-registration side effects)
from card import ID_TO_CARD, CardPile, Targeting
from character import encounters as encounters_module
from character.core import Character
from character.enemy import ID_TO_ENEMY, Enemy
from character.player import ID_TO_PLAYER, Player
from fight import Fight
from util.effect import ID_TO_EFFECT, Effect

# The action tuple stored for "end your turn" rather than playing a card.
END_TURN_ACTION = (-1,)


def _encounter_metadata() -> list[dict]:
    """One entry per encounter builder in encounters.py: the builder plus per-slot enemy info.

    ALL_ENCOUNTERS supplies the canonical ordering; builders defined in the module but not
    listed there (e.g. multi-enemy encounters) are appended alphabetically. The encounter id
    used throughout the viewer is the index into this list.
    """
    builders = list(encounters_module.ALL_ENCOUNTERS)
    builders += [
        fn
        for _, fn in inspect.getmembers(encounters_module, inspect.isfunction)
        if fn.__module__ == encounters_module.__name__ and fn not in builders
    ]
    metadata = []
    for builder in builders:
        slots = [
            # Enemy.__post_init__ does not chain to Character.__post_init__, so enemies built
            # without an explicit name have name=None; fall back to the class name.
            {"enemy_id": enemy.id, "name": enemy.name or type(enemy).__name__, "default_intent": enemy.intent.id}
            for enemy in builder()
        ]
        metadata.append({"builder": builder, "name": builder.__name__.replace("_", " ").title(), "slots": slots})
    return metadata


ENCOUNTERS = _encounter_metadata()


def player_classes() -> dict[int, str]:
    """Player ids that the engine can actually reconstruct, mapped to their class name."""
    return {pid: cls.__name__ for pid, cls in ID_TO_PLAYER.items()}


def enemy_classes() -> dict[int, str]:
    """Enemy ids the engine knows about, mapped to their class name."""
    return {eid: cls.__name__ for eid, cls in ID_TO_ENEMY.items()}


def encounter_list() -> dict[int, dict]:
    """Encounter ids mapped to display data: the encounter name and one entry per enemy slot."""
    return {
        idx: {
            "name": enc["name"],
            "enemies": [{"id": slot["enemy_id"], "name": slot["name"]} for slot in enc["slots"]],
        }
        for idx, enc in enumerate(ENCOUNTERS)
    }


def encounter_size(encounter_id: int) -> int:
    """The number of enemy slots in an encounter, dead or alive."""
    return len(ENCOUNTERS[encounter_id]["slots"])


def enemy_names(encounter_id: int, alive_slots: list[int]) -> list[str]:
    """Display names of the living enemies, aligned with their order in Fight.enemies."""
    slots = ENCOUNTERS[encounter_id]["slots"]
    return [slots[i]["name"] for i in alive_slots]


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
    encounter_id: int,
    turn: int = 0,
    player_hp: int | None = None,
    player_block: int = 0,
    player_energy: int = 3,
    player_stars: int | None = None,
    draw: dict[int, int] | None = None,
    hand: dict[int, int] | None = None,
    discard: dict[int, int] | None = None,
    player_effects: dict[int, dict[str, int]] | None = None,
    enemies: list[dict] | None = None,
) -> Fight:
    """Reconstruct a Fight from form inputs.

    ``enemies`` holds one spec per encounter slot ({"hp", "block", "intent", "effects"}); slots
    whose hp is 0 or less are dead and excluded from the fight, matching how the search removes
    dead enemies (so ``Fight.to_vector()`` omits them). ``None`` builds the encounter fresh,
    with each enemy's rolled hp and starting intent.
    """
    if player_id not in ID_TO_PLAYER:
        raise ValueError(f"No engine support for player id {player_id}")
    if encounter_id is None or not 0 <= encounter_id < len(ENCOUNTERS):
        raise ValueError(f"No encounter with id {encounter_id}")

    player: Player = ID_TO_PLAYER[player_id](
        block=player_block,
        energy=player_energy,
        effects=_build_effects(player_effects or {}),
        hand=_build_pile(hand or {}),
        discard_pile=_build_pile(discard or {}),
    )

    if player_hp is not None:
        player.hp = player_hp
    if player_stars is not None:
        player.stars = player_stars
    if draw is not None:
        player.draw_pile = _build_pile(draw)

    slot_enemies: list[Enemy] = ENCOUNTERS[encounter_id]["builder"]()
    if enemies is None:
        fight_enemies = slot_enemies
    else:
        if len(enemies) != len(slot_enemies):
            raise ValueError(f"Encounter {encounter_id} needs {len(slot_enemies)} enemy specs, got {len(enemies)}")
        fight_enemies = []
        for enemy, spec in zip(slot_enemies, enemies):
            if spec["hp"] <= 0:
                continue
            enemy.hp = spec["hp"]
            enemy.block = spec.get("block", 0)
            enemy.effects = _build_effects(spec.get("effects") or {})
            if spec.get("intent") is not None:
                enemy.intent = type(enemy).id_to_intent(spec["intent"])
            fight_enemies.append(enemy)
        if not fight_enemies:
            raise ValueError("At least one enemy must be alive (hp > 0)")

    fight = Fight(player=player, enemies=fight_enemies, turn=turn or 0)
    return fight


def action_label(action: tuple[int, ...], enemy_names: list[str] | None = None) -> str:
    """Human-readable label for a stored action tuple: (action_id,) or (action_id, target_index).

    ``enemy_names`` are the living enemies' display names, aligned with their target indices.
    """
    if tuple(action) == END_TURN_ACTION:
        return "End turn"
    action_id = action[0]
    label = ID_TO_CARD[action_id].__name__ if action_id in ID_TO_CARD else f"Action {action_id}"
    if len(action) > 1:
        target = action[1]
        if enemy_names and 0 <= target < len(enemy_names):
            label += f" → {enemy_names[target]}"
        else:
            label += f" → enemy {target}"
    return label


def describe_form(fight: Fight, encounter_id: int, alive_slots: list[int]) -> dict:
    """Decompose a Fight back into the values of the web form's fields, so a successor state
    can be loaded into the form and re-queried.

    ``alive_slots`` maps each entry of ``fight.enemies`` to its encounter slot. Dead slots are
    still emitted (with hp 0) so their form panels persist across states.
    """
    player = fight.player
    if len(alive_slots) != len(fight.enemies):
        raise ValueError(f"Expected {len(fight.enemies)} alive slots, got {len(alive_slots)}")

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

    empty_effects = {eid: {"present": False, "power": 0, "duration": 0} for eid in effect_types()}
    enemy_specs = [
        {"hp": 0, "block": 0, "intent": slot["default_intent"], "effects": empty_effects}
        for slot in ENCOUNTERS[encounter_id]["slots"]
    ]
    for slot_index, enemy in zip(alive_slots, fight.enemies):
        enemy_specs[slot_index] = {
            "hp": enemy.hp,
            "block": enemy.block,
            "intent": enemy.intent.id,
            "effects": effect_specs(enemy),
        }

    return {
        "player": player.id,
        "encounter": encounter_id,
        "turn": fight.turn,
        "player_hp": player.hp,
        "player_block": player.block,
        "player_energy": player.energy,
        "player_stars": player.stars,
        "player_effects": effect_specs(player),
        "enemies": enemy_specs,
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


def _outcome(fight: Fight, prob: Fraction, label: str, encounter_id: int, alive_slots: list[int]) -> dict:
    return {
        "prob": prob,
        "state_key": tuple(int(x) for x in fight.to_vector()),
        "label": label,
        "encounter": encounter_id,
        "alive_slots": list(alive_slots),
        "form": describe_form(fight, encounter_id, alive_slots),
    }


def _turn_start_outcomes(
    fight: Fight,
    encounter_id: int,
    alive_slots: list[int],
    prob: Fraction = Fraction(1),
    label_suffix: str = "",
) -> list[dict]:
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
        outcomes.append(
            _outcome(fight, prob * draw_prob, f"Draw {_pile_label(hand)}" + label_suffix, encounter_id, alive_slots)
        )
    return outcomes


def start_of_turn(fight: Fight, encounter_id: int, alive_slots: list[int]) -> dict:
    """Resolve the start of the player's turn directly from a state, without playing an action.

    Lets the user view every possible draw from the current fight state — e.g. all opening
    hands, by staging from the pre-first-turn state (turn 0, full draw pile, empty hand).
    Returns the same shape as advance_state, plus the number of the turn being started.
    """
    if fight.is_over():
        raise ValueError("The fight is already over in this state")
    outcomes = _turn_start_outcomes(fight, encounter_id, alive_slots)
    return {"hp_lost": 0, "terminal": None, "turn": fight.turn, "outcomes": outcomes}


def advance_state(
    state_key: tuple[int, ...], action: tuple[int, ...], encounter_id: int, alive_slots: list[int]
) -> dict:
    """Advance a state by one action, returning the distribution of successor states.

    The action is (action_id,) for untargeted actions, (action_id, target_index) for targeted
    ones, or END_TURN_ACTION. ``alive_slots`` maps each enemy encoded in the state to its
    encounter slot, since dead enemies are excluded from the vector.

    Mirrors the sequencing of the search methods in fight.py (search_player_turn_action →
    search_player_turn_end → search_enemy_turn_start/…/_end → search_player_turn_start),
    calling the same engine methods in the same order — including removing enemies killed by a
    card play — so successor keys match the keys the solver wrote into the dp table.

    Returns {"hp_lost": int, "terminal": "victory" | "defeat" | None, "outcomes": [...]}.
    A card play yields one outcome; ending the turn branches over the enemies' next intents
    and the player's possible draws.
    """
    fight, _ = Fight.from_vector(tuple(state_key))
    if encounter_id not in range(len(ENCOUNTERS)):
        raise ValueError(f"No encounter with id {encounter_id}")
    if len(alive_slots) != len(fight.enemies):
        raise ValueError(f"Expected {len(fight.enemies)} alive slots, got {len(alive_slots)}")
    if any(slot not in range(encounter_size(encounter_id)) for slot in alive_slots):
        raise ValueError(f"Alive slots {alive_slots} out of range for encounter {encounter_id}")
    player = fight.player
    hp_start = player.hp

    if action != END_TURN_ACTION:
        action_id = action[0]
        target_index = action[1] if len(action) > 1 else None
        if action_id not in ID_TO_CARD:
            raise ValueError(f"Unknown action id {action_id}")
        card = ID_TO_CARD[action_id]()
        if player.hand.cards[card] == 0:
            raise ValueError(f"{card} is not in the player's hand")
        if not player.can_play(card):
            raise ValueError(f"Not enough energy to play {card}")

        if card.targeting == Targeting.ENEMY_SINGLE:
            if target_index is None or not 0 <= target_index < len(fight.enemies):
                raise ValueError(f"{card} requires an enemy target, got {target_index}")
            player.play(card, fight.enemies[target_index])
        else:
            player.play(card)

        # Mirror search_player_turn_action: enemies killed by the play leave the fight (and
        # therefore the state vector), while their form slots stay behind as dead.
        alive_slots = [slot for slot, enemy in zip(alive_slots, fight.enemies) if enemy.hp > 0]
        fight.enemies = [enemy for enemy in fight.enemies if enemy.hp > 0]

        hp_lost = hp_start - player.hp
        if fight.is_over():
            terminal = "defeat" if player.hp <= 0 else "victory"
            return {"hp_lost": hp_lost, "terminal": terminal, "outcomes": []}
        return {
            "hp_lost": hp_lost,
            "terminal": None,
            "outcomes": [_outcome(fight, Fraction(1), f"After playing {card}", encounter_id, alive_slots)],
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

    # Intent transition, exactly as search_enemy_turn_end branches it: next intents are
    # captured before end-of-turn resolution, then every combination becomes one branch.
    next_intent_options = [enemy.intent.next_intents() for enemy in fight.enemies]
    branching_intents = any(len(options) > 1 for options in next_intent_options)
    for enemy in fight.enemies:
        enemy.resolve_end_of_turn()
    mid_vector = fight.to_vector()
    outcomes = []
    for combo in product(*next_intent_options):
        branch, _ = Fight.from_vector(mid_vector)
        combo_prob = Fraction(1)
        for enemy, (next_intent, intent_prob) in zip(branch.enemies, combo):
            combo_prob *= intent_prob
            enemy.intent = next_intent
        suffix = " — intent: " + ", ".join(str(next_intent) for next_intent, _ in combo) if branching_intents else ""
        outcomes.extend(_turn_start_outcomes(branch, encounter_id, alive_slots, combo_prob, suffix))

    return {"hp_lost": hp_lost, "terminal": None, "outcomes": outcomes}
