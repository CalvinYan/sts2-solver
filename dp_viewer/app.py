# type: ignore
"""Flask app for browsing the solved dp table.

The user describes a fight (player class, encounter, turn, resources, and card piles); the app
reconstructs the corresponding state vector via the engine and returns the stored map of
actions to their HP-loss probability distributions, cheapest expected loss first.
"""

from __future__ import annotations

import os
from fractions import Fraction

import state as state_bridge
from flask import Flask, jsonify, render_template, request

from fight import Fight
from search.table import QTable

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "solver",
    "ironclad-base",
    "toadpoles_22_22.csv.pkl.gz",
)

app = Flask(__name__)

# Loaded once at import time. The dp data never changes at runtime.
table = QTable.load(DATA_PATH)


def _expected(distribution: dict[int, Fraction]) -> Fraction:
    return sum((Fraction(loss) * prob for loss, prob in distribution.items()), start=Fraction(0))


def _distribution_payload(distribution: dict[int, Fraction]) -> dict:
    """Turn a {hp_loss: Fraction} distribution into JSON-friendly, display-ready data."""
    outcomes = [
        {"hp_loss": loss, "prob": float(prob), "prob_str": str(prob)} for loss, prob in sorted(distribution.items())
    ]
    return {"expected_loss": float(_expected(distribution)), "outcomes": outcomes}


def _state_value_payload(state_key: tuple[int, ...], enemy_names: list[str] | None = None) -> dict:
    """The solved value of a state: the HP-loss distribution of its best stored action."""
    stored = table.actions_for(state_key)
    if not stored:
        return {"found": False}
    best_action, best_dist = min(stored.items(), key=lambda item: _expected(item[1]))
    return {
        "found": True,
        "best_action": state_bridge.action_label(best_action, enemy_names),
        **_distribution_payload(best_dist),
    }


def _pile_from_request(prefix: str) -> dict[int, int]:
    """Read per-card counts for a pile, e.g. draw_0, draw_1, ... into {card_id: count}."""
    counts: dict[int, int] = {}
    for card_id in state_bridge.card_ids():
        counts[card_id] = request.args.get(f"{prefix}_{card_id}", 0, type=int)
    return counts


def _effects_from_request(prefix: str) -> dict[int, dict[str, int]]:
    """Read per-effect stats for a character, e.g. peff_0_power, peff_2_duration."""
    specs: dict[int, dict[str, int]] = {}
    for effect_id, meta in state_bridge.effect_types().items():
        entry: dict[str, int] = {}
        entry["present"] = request.args.get(f"{prefix}_{effect_id}_present", default=False, type=bool)
        if meta["power"]:
            entry["power"] = request.args.get(f"{prefix}_{effect_id}_power", 0, type=int)
        if meta["duration"]:
            entry["duration"] = request.args.get(f"{prefix}_{effect_id}_duration", 0, type=int)
        specs[effect_id] = entry
    return specs


@app.route("/")
def index():
    encounters = state_bridge.encounter_list()
    return render_template(
        "index.html",
        players=state_bridge.player_classes(),
        encounters=encounters,
        max_slots=max(len(enc["enemies"]) for enc in encounters.values()),
        cards=state_bridge.card_ids(),
        effects=state_bridge.effect_types(),
        intents={eid: state_bridge.enemy_intents(eid) for eid in state_bridge.enemy_classes()},
        row_count=len(table),
    )


def _form_fields(form: dict) -> dict[str, int]:
    """Flatten describe_form() output into {form-input-name: value} for the front end."""
    fields: dict[str, int] = {
        name: form[name]
        for name in (
            "player",
            "encounter",
            "turn",
            "player_hp",
            "player_block",
            "player_energy",
            "player_stars",
        )
    }
    for prefix in ("draw", "hand", "discard"):
        for card_id, count in form[prefix].items():
            fields[f"{prefix}_{card_id}"] = count

    effect_meta = state_bridge.effect_types()

    def flatten_effects(prefix: str, specs: dict) -> None:
        for effect_id, vals in specs.items():
            fields[f"{prefix}_{effect_id}_present"] = vals["present"]
            if effect_meta[effect_id]["power"]:
                fields[f"{prefix}_{effect_id}_power"] = vals["power"]
            if effect_meta[effect_id]["duration"]:
                fields[f"{prefix}_{effect_id}_duration"] = vals["duration"]

    flatten_effects("peff", form["player_effects"])
    for slot, spec in enumerate(form["enemies"]):
        fields[f"e{slot}_hp"] = spec["hp"]
        fields[f"e{slot}_block"] = spec["block"]
        fields[f"e{slot}_intent"] = spec["intent"]
        flatten_effects(f"e{slot}eff", spec["effects"])
    return fields


def _outcomes_payload(outcomes: list[dict]) -> list[dict]:
    return [
        {
            "prob": float(o["prob"]),
            "prob_str": str(o["prob"]),
            "label": o["label"],
            "form": _form_fields(o["form"]),
            "value": _state_value_payload(o["state_key"], state_bridge.enemy_names(o["encounter"], o["alive_slots"])),
        }
        for o in outcomes
    ]


def _enemy_specs_from_request(encounter_id: int) -> list[dict]:
    """Read per-slot enemy fields, e.g. e0_hp, e1_intent, e0eff_3_power, into one spec per slot."""
    return [
        {
            "hp": request.args.get(f"e{slot}_hp", 0, type=int),
            "block": request.args.get(f"e{slot}_block", 0, type=int),
            "intent": request.args.get(f"e{slot}_intent", 0, type=int),
            "effects": _effects_from_request(f"e{slot}eff"),
        }
        for slot in range(state_bridge.encounter_size(encounter_id))
    ]


def _fight_from_request() -> tuple[Fight, int, list[int]]:
    """Build the Fight described by the form, plus its encounter id and the slots still alive."""
    encounter_id = request.args.get("encounter", type=int)
    if encounter_id is None:
        raise ValueError("No encounter selected")
    enemy_specs = _enemy_specs_from_request(encounter_id)
    fight = state_bridge.build_fight(
        player_id=request.args.get("player", type=int),
        encounter_id=encounter_id,
        turn=request.args.get("turn", 1, type=int),
        player_hp=request.args.get("player_hp", 0, type=int),
        player_block=request.args.get("player_block", 0, type=int),
        player_energy=request.args.get("player_energy", 0, type=int),
        player_stars=request.args.get("player_stars", 0, type=int),
        draw=_pile_from_request("draw"),
        hand=_pile_from_request("hand"),
        discard=_pile_from_request("discard"),
        player_effects=_effects_from_request("peff"),
        enemies=enemy_specs,
    )
    alive_slots = [slot for slot, spec in enumerate(enemy_specs) if spec["hp"] > 0]
    return fight, encounter_id, alive_slots


@app.route("/advance", methods=["POST"])
def advance():
    payload = request.get_json(silent=True) or {}
    try:
        state_key = tuple(int(x) for x in payload["state_key"])
        action = tuple(int(x) for x in payload["action"])
        encounter_id = int(payload["encounter"])
        alive_slots = [int(x) for x in payload["alive_slots"]]
        result = state_bridge.advance_state(state_key, action, encounter_id, alive_slots)
    except (ValueError, KeyError, TypeError, IndexError) as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(
        {
            "hp_lost": result["hp_lost"],
            "terminal": result["terminal"],
            "outcomes": _outcomes_payload(result["outcomes"]),
        }
    )


@app.route("/start_turn")
def start_turn():
    try:
        fight, encounter_id, alive_slots = _fight_from_request()
        result = state_bridge.start_of_turn(fight, encounter_id, alive_slots)
    except (ValueError, KeyError, TypeError, IndexError) as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(
        {
            "hp_lost": result["hp_lost"],
            "terminal": result["terminal"],
            "turn": result["turn"],
            "outcomes": _outcomes_payload(result["outcomes"]),
        }
    )


@app.route("/reset")
def reset_encounter():
    try:
        encounter_id = request.args.get("encounter", type=int)
        fight = state_bridge.build_fight(player_id=request.args.get("player", type=int), encounter_id=encounter_id)
        alive_slots = list(range(state_bridge.encounter_size(encounter_id)))
        result = state_bridge._outcome(fight, Fraction(1), "Start of fight", encounter_id, alive_slots)
    except (ValueError, KeyError, TypeError, IndexError) as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(
        {
            "outcomes": _outcomes_payload([result]),
        }
    )


@app.route("/query")
def query():
    try:
        fight, encounter_id, alive_slots = _fight_from_request()
        state_key = fight.to_vector()
        stored = table.actions_for(state_key)
    except (ValueError, KeyError, TypeError, IndexError) as e:
        return jsonify({"error": str(e)}), 400

    names = state_bridge.enemy_names(encounter_id, alive_slots)
    actions = [
        {"action": action, "label": state_bridge.action_label(action, names), **_distribution_payload(dist)}
        for action, dist in stored.items()
    ]
    actions.sort(key=lambda a: a["expected_loss"])
    if actions:
        actions[0]["best"] = True

    return jsonify(
        {
            "found": bool(actions),
            "state_key": list(state_key),
            "alive_slots": alive_slots,
            "actions": actions,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
