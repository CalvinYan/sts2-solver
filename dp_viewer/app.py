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

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dp_data.csv")

app = Flask(__name__)

# Loaded once at import time (~15s, ~220MB). The dp data never changes at runtime.
dp_table = DpTable.load(DATA_PATH)


def _distribution_payload(distribution: dict[int, Fraction]) -> dict:
    """Turn a {hp_loss: Fraction} distribution into JSON-friendly, display-ready data."""
    expected = sum((Fraction(loss) * prob for loss, prob in distribution.items()), start=Fraction(0))
    outcomes = [
        {"hp_loss": loss, "prob": float(prob), "prob_str": str(prob)} for loss, prob in sorted(distribution.items())
    ]
    return {"expected_loss": float(expected), "outcomes": outcomes}


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


@app.route("/query")
def query():
    try:
        state_key = state_bridge.build_state_key(
            player_id=request.args.get("player", type=int),
            enemy_id=request.args.get("enemy", type=int),
            turn=request.args.get("turn", 1, type=int),
            player_hp=request.args.get("player_hp", 0, type=int),
            player_block=request.args.get("player_block", 0, type=int),
            player_energy=request.args.get("player_energy", 0, type=int),
            enemy_hp=request.args.get("enemy_hp", 0, type=int),
            enemy_block=request.args.get("enemy_block", 0, type=int),
            enemy_intent=request.args.get("enemy_intent", 0, type=int),
            draw=_pile_from_request("draw"),
            hand=_pile_from_request("hand"),
            discard=_pile_from_request("discard"),
            player_effects=_effects_from_request("peff"),
            enemy_effects=_effects_from_request("eeff"),
        )
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": str(e)}), 400

    stored = dp_table.actions_for(state_key)
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
