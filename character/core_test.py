import numpy as np

from character.core import Character
from util.core import Action
from util.effect import Frail, Strength, Thorns, Vulnerable, Weak


def test_character_encodes_to_vector():
    c = Character(name="Test", id=0, hp=80)

    # Apply some effects
    c.receive_effects([Strength(power=2)])
    c.receive_effects([Vulnerable(duration=2)])

    expected = (
        0,
        80,
        0,
        1,
        2,
        0,
        0,
        0,
        0,
        1,
        0,
        2,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    got = c.to_vector()

    assert np.array_equal(expected, got)


def test_character_with_no_effects_encodes_to_vector():
    c = Character(name="Test", id=0, hp=80)

    expected = (
        0,
        80,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    got = c.to_vector()

    assert np.array_equal(expected, got)


def test_character_with_negative_hp_encodes_to_vector():
    c = Character(name="Test", id=0, hp=-15)

    expected = (
        0,
        -15,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    got = c.to_vector()

    assert np.array_equal(expected, got)


def test_no_character_encodes_to_zeroes():
    expected = (
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    got = Character.to_vector(None)

    assert np.array_equal(expected, got)


def test_character_decodes_from_vector():
    vector = (0, 40, 10, 1, 7, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    expected = Character(name="Character", id=0, hp=40, block=10, effects=[Strength(power=7), Vulnerable(duration=1)])
    got, read = Character.from_vector(vector)
    assert expected == got
    assert len(vector) == read


def test_character_round_trip():
    expected = Character(name="Character", id=1, hp=24, block=0, effects=[Weak(duration=5)])
    got, _ = Character.from_vector(tuple(expected.to_vector()))
    assert expected == got


def test_character_effects_stack():
    c = Character(name="Test", id=0, hp=80)

    c.receive_effects([Strength(power=2)])
    c.receive_effects([Strength(power=2)])

    assert len(c.effects) == 1
    assert c.effects[0] == Strength(power=4)


def test_character_loses_block():
    c = Character(name="Test", id=0, hp=80, block=10)

    c.resolve_start_of_turn()

    assert c.block == 0


def test_character_effects_tick_down():
    c = Character(name="Test", id=0, hp=80)

    c.receive_effects([Weak(duration=2)])

    assert len(c.effects) == 1
    assert c.effects[0] == Weak(duration=2)

    c.resolve_end_of_turn()

    assert len(c.effects) == 1
    assert c.effects[0] == Weak(duration=1)

    c.resolve_end_of_turn()

    assert len(c.effects) == 0


def test_character_full_block():
    c = Character(name="Test", id=0, hp=80, block=10)

    c.take_damage(7)

    assert c.hp == 80


def test_character_take_damage():
    c = Character(name="Test", id=0, hp=80)

    c.take_damage(10)

    assert c.hp == 70


def test_character_take_damage_through_block():
    c = Character(name="Test", id=0, hp=80, block=29)

    c.take_damage(33)

    assert c.hp == 76


def test_character_act_resolve_all_effects():
    attacker = Character(
        name="Attacker",
        id=0,
        hp=0,
        effects=[Strength(power=4), Frail(duration=2), Weak(duration=2)],
    )
    defender = Character(
        name="Defender",
        id=0,
        hp=0,
        effects=[Thorns(power=5), Vulnerable(duration=2)],
    )
    action = Action(damage=10, block=5)

    attacker.act(defender, action)

    assert attacker.hp == -5
    assert defender.hp == -15
    assert attacker.block == 3


def test_character_act_apply_effects():
    actor_effects = [Strength(power=2)]
    target_effects = [Vulnerable(duration=1), Weak(duration=1)]
    attacker = Character(name="Attacker", id=0, hp=0)
    defender = Character(name="Defender", id=0, hp=0)
    action = Action(actor_effects=actor_effects, target_effects=target_effects)

    attacker.act(defender, action)

    assert attacker.effects == actor_effects
    assert defender.effects == target_effects
