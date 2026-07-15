# type: ignore
"""Flask app for browsing the solved dp table.

The user describes a fight (player class, enemy, turn, resources, and card piles); the app
reconstructs the corresponding state vector via the engine and returns the stored map of
actions to their HP-loss probability distributions, cheapest expected loss first.
"""

from __future__ import annotations

import os
from fractions import Fraction

import state as state_bridge
from flask import Flask, jsonify, render_template, request
from table import DpTable

from fight import Fight

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "solver",
    "all.csv.pkl.gz",
)

app = Flask(__name__)

# Loaded once at import time. The dp data never changes at runtime.
dp_table = DpTable.load(DATA_PATH)


def _expected(distribution: dict[int, Fraction]) -> Fraction:
    return sum((Fraction(loss) * prob for loss, prob in distribution.items()), start=Fraction(0))


def _distribution_payload(distribution: dict[int, Fraction]) -> dict:
    """Turn a {hp_loss: Fraction} distribution into JSON-friendly, display-ready data."""
    outcomes = [
        {"hp_loss": loss, "prob": float(prob), "prob_str": str(prob)} for loss, prob in sorted(distribution.items())
    ]
    return {"expected_loss": float(_expected(distribution)), "outcomes": outcomes}


def _state_value_payload(state_key: tuple[int, ...]) -> dict:
    """The solved value of a state: the HP-loss distribution of its best stored action."""
    stored = dp_table.actions_for(state_key)
    if not stored:
        return {"found": False}
    best_id, best_dist = min(stored.items(), key=lambda item: _expected(item[1]))
    return {"found": True, "best_action": state_bridge.action_label(best_id), **_distribution_payload(best_dist)}


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
    return render_template(
        "index.html",
        players=state_bridge.player_classes(),
        enemies=state_bridge.enemy_classes(),
        cards=state_bridge.card_ids(),
        effects=state_bridge.effect_types(),
        intents={eid: state_bridge.enemy_intents(eid) for eid in state_bridge.enemy_classes()},
        state_count=dp_table.state_count,
    )


def _form_fields(form: dict) -> dict[str, int]:
    """Flatten describe_form() output into {form-input-name: value} for the front end."""
    fields: dict[str, int] = {
        name: form[name]
        for name in (
            "player",
            "enemy",
            "turn",
            "player_hp",
            "player_block",
            "player_energy",
            "player_stars",
            "enemy_hp",
            "enemy_block",
            "enemy_intent",
        )
    }
    for prefix in ("draw", "hand", "discard"):
        for card_id, count in form[prefix].items():
            fields[f"{prefix}_{card_id}"] = count
    effect_meta = state_bridge.effect_types()
    for prefix, key in (("peff", "player_effects"), ("eeff", "enemy_effects")):
        for effect_id, vals in form[key].items():
            fields[f"{prefix}_{effect_id}_present"] = vals["present"]
            if effect_meta[effect_id]["power"]:
                fields[f"{prefix}_{effect_id}_power"] = vals["power"]
            if effect_meta[effect_id]["duration"]:
                fields[f"{prefix}_{effect_id}_duration"] = vals["duration"]
    return fields


def _outcomes_payload(outcomes: list[dict]) -> list[dict]:
    return [
        {
            "prob": float(o["prob"]),
            "prob_str": str(o["prob"]),
            "label": o["label"],
            "form": _form_fields(o["form"]),
            "value": _state_value_payload(o["state_key"]),
        }
        for o in outcomes
    ]


def _fight_from_request() -> Fight:
    return state_bridge.build_fight(
        player_id=request.args.get("player", type=int),
        enemy_id=request.args.get("enemy", type=int),
        turn=request.args.get("turn", 1, type=int),
        player_hp=request.args.get("player_hp", 0, type=int),
        player_block=request.args.get("player_block", 0, type=int),
        player_energy=request.args.get("player_energy", 0, type=int),
        player_stars=request.args.get("player_stars", 0, type=int),
        enemy_hp=request.args.get("enemy_hp", 0, type=int),
        enemy_block=request.args.get("enemy_block", 0, type=int),
        enemy_intent=request.args.get("enemy_intent", 0, type=int),
        draw=_pile_from_request("draw"),
        hand=_pile_from_request("hand"),
        discard=_pile_from_request("discard"),
        player_effects=_effects_from_request("peff"),
        enemy_effects=_effects_from_request("eeff"),
    )


@app.route("/advance", methods=["POST"])
def advance():
    payload = request.get_json(silent=True) or {}
    try:
        state_key = tuple(int(x) for x in payload["state_key"])
        action_id = int(payload["action_id"])
        result = state_bridge.advance_state(state_key, action_id)
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
        fight = _fight_from_request()
        result = state_bridge.start_of_turn(fight)
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
        fight = state_bridge.build_fight(
            player_id=request.args.get("player", type=int), enemy_id=request.args.get("enemy", type=int)
        )
        result = state_bridge._outcome(fight, Fraction(1), "Start of fight")
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
        fight = _fight_from_request()
        state_key = fight.to_vector()
        stored = dp_table.actions_for(state_key)
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": str(e)}), 400

    actions = [
        {"action_id": action_id, "label": state_bridge.action_label(action_id), **_distribution_payload(dist)}
        for action_id, dist in stored.items()
    ]
    actions.sort(key=lambda a: a["expected_loss"])
    if actions:
        actions[0]["best"] = True

    return jsonify({"found": bool(actions), "state_key": list(state_key), "actions": actions})


if __name__ == "__main__":
    app.run(debug=True)
