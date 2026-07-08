import numpy as np

from character.core import Character
from util.core import Action
from util.effect import Frail, Strength, Thorns, Vulnerable, Weak


def test_character_encodes_to_vector():
    c = Character(name="Test", id=0, hp=80)

    # Apply some buffs and debuffs
    c.receive_buffs([Strength(power=2)])
    c.receive_debuffs([Vulnerable(duration=2)])

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


def test_character_with_no_debuffs_encodes_to_vector():
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


def test_character_buffs_stack():
    c = Character(name="Test", id=0, hp=80)

    c.receive_buffs([Strength(power=2)])
    c.receive_buffs([Strength(power=2)])

    assert len(c.buffs) == 1
    assert c.buffs[0] == Strength(power=4)


def test_character_buffs_dont_stack_with_debuffs():
    c = Character(name="Test", id=0, hp=80)

    c.receive_buffs([Strength(power=2)])
    c.receive_debuffs([Strength(power=2)])

    assert len(c.buffs) == 1
    assert c.buffs[0] == Strength(power=2)

    assert len(c.debuffs) == 1
    assert c.debuffs[0] == Strength(power=2)


def test_character_loses_block():
    c = Character(name="Test", id=0, hp=80, block=10)

    c.resolve_start_of_turn(None)

    assert c.block == 0


def test_character_effects_tick_down():
    c = Character(name="Test", id=0, hp=80)

    c.receive_debuffs([Weak(duration=2)])

    assert len(c.debuffs) == 1
    assert c.debuffs[0] == Weak(duration=2)

    c.resolve_end_of_turn(None)

    assert len(c.debuffs) == 1
    assert c.debuffs[0] == Weak(duration=1)

    c.resolve_end_of_turn(None)

    assert len(c.debuffs) == 0


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
        buffs=[Strength(power=4)],
        debuffs=[Frail(duration=2), Weak(duration=2)],
    )
    defender = Character(
        name="Defender",
        id=0,
        hp=0,
        buffs=[Thorns(power=5)],
        debuffs=[Vulnerable(duration=2)],
    )
    action = Action(damage=10, block=5)

    attacker.act(defender, action)

    assert attacker.hp == -5
    assert defender.hp == -15
    assert attacker.block == 3


def test_character_act_apply_effects():
    buffs = [Strength(power=2)]
    debuffs = [Vulnerable(duration=1), Weak(duration=1)]
    attacker = Character(name="Attacker", id=0, hp=0)
    defender = Character(name="Defender", id=0, hp=0)
    action = Action(buffs=buffs, debuffs=debuffs)

    attacker.act(defender, action)

    assert attacker.buffs == buffs
    assert defender.debuffs == debuffs
