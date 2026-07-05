from character.core import Character
from util.core import Action, Move
from util.effect import Effect, Frail, Shrink, Strength, Thorns, Vulnerable, Weak

def test_strength_increment_damage_dealt():
    action = Action(damage=5)
    Strength(power=2).resolve(Move(action, None, None), False)

    assert action.damage == 7

def test_strength_no_increment_damage_received():
    action = Action(damage=5)
    Strength(power=2).resolve(Move(action, None, None), True)

    assert action.damage == 5

def test_vuln_multiply_damage_received():
    action = Action(damage=12)
    Vulnerable(duration=2).resolve(Move(action, None, None), True)

    assert action.damage == 18

def test_vuln_no_multiply_damage_dealt():
    action = Action(damage=12)
    Vulnerable(duration=2).resolve(Move(action, None, None), False)

    assert action.damage == 12

def test_vuln_no_increase_with_power():
    action = Action(damage=12)
    Vulnerable(duration=2, power=100000).resolve(Move(action, None, None), True)

    assert action.damage == 18

def test_thorns_damages_attacker():
    c1 = Character(name="Attacker", id=0, hp=0)
    c2 = Character(name="Defender", id=0, hp=0)
    action = Action(damage=1)
    Thorns(power=2).resolve(Move(action, c1, c2), True)

    assert c1.hp == -2

def test_thorns_no_damage_defender():
    c1 = Character(name="Attacker", id=0, hp=0)
    c2 = Character(name="Defender", id=0, hp=0)
    action = Action(damage=1)
    Thorns(power=2).resolve(Move(action, c1, c2), False)

    assert c1.hp == 0

def test_weak_reduce_damage_dealt():
    action = Action(damage=12)
    Weak(duration=2).resolve(Move(action, None, None), False)

    assert action.damage == 9

def test_weak_no_reduce_damage_received():
    action = Action(damage=12)
    Weak(duration=2).resolve(Move(action, None, None), True)

    assert action.damage == 12

def test_weak_no_increase_with_power():
    action = Action(damage=12)
    Weak(duration=2, power=100000).resolve(Move(action, None, None), False)

    assert action.damage == 9

def test_frail_reduce_block_gained():
    action = Action(block=8)
    Frail(duration=2).resolve(Move(action, None, None), False)

    assert action.block == 6

def test_shrink_reduce_damage_dealt():
    action = Action(damage=8)
    Shrink(duration=2).resolve(Move(action, None, None), False)

    assert action.damage == 5

def test_shrink_no_reduce_damage_received():
    action = Action(damage=8)
    Shrink(duration=2).resolve(Move(action, None, None), True)

    assert action.damage == 8

def test_shrink_no_increase_with_power():
    action = Action(damage=8)
    Shrink(duration=2, power=100000).resolve(Move(action, None, None), False)

    assert action.damage == 5

def test_strength_only_affects_attacks():
    action = Action(block=5)
    Strength(power=100).resolve(Move(action, None, None), False)

    assert action.damage == None

def test_effects_encode_to_vector():
    effects = [Strength(power=2), Thorns(power=2), Vulnerable(duration=4), Weak(duration=1)]
    for effect, expected in zip(
        effects,
        [
            (1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (0, 0, 0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0, 0, 1, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0),
        ]
    ):
        assert expected == effect.to_vector()

def test_effects_list_encodes_to_vector():
    effects = [Strength(power=2), Thorns(power=2), Vulnerable(duration=4), Weak(duration=1)]
    expected = (1, 2, 0, 1, 2, 0, 1, 0, 4, 1, 0, 1, 0, 0, 0, 0, 0, 0)
    got = Effect.effects_to_vector(effects)
    assert expected == got