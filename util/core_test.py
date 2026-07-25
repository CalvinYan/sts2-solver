from copy import deepcopy

from util.core import Action
from util.effect import Strength, Vulnerable, Weak


def test_action_deepcopy_equals_original():
    action = Action(
        damage=6,
        block=5,
        stars_gained=2,
        actor_effects=[Strength(power=2)],
        target_effects=[Vulnerable(duration=1), Weak(duration=1)],
    )

    got = deepcopy(action)

    assert got == action
    assert got is not action


def test_action_deepcopy_does_not_share_effects():
    strength = Strength(power=2)
    vulnerable = Vulnerable(duration=1)
    action = Action(damage=6, actor_effects=[strength], target_effects=[vulnerable])

    got = deepcopy(action)
    # Effects are mutated when they stack onto a character, so a copy must own its own
    got.damage = 99
    got.actor_effects[0].power = 99
    got.target_effects[0].duration = 99
    got.target_effects.append(Weak(duration=1))

    assert action.damage == 6
    assert strength == Strength(power=2)
    assert vulnerable == Vulnerable(duration=1)
    assert action.target_effects == [Vulnerable(duration=1)]


def test_action_deepcopy_preserves_effect_types():
    action = Action(actor_effects=[Strength(power=2)], target_effects=[Vulnerable(duration=1)])

    got = deepcopy(action)

    assert [type(effect) for effect in got.actor_effects] == [Strength]
    assert [type(effect) for effect in got.target_effects] == [Vulnerable]


def test_action_deepcopy_respects_memo():
    action = Action(damage=6, actor_effects=[Strength(power=2)])

    # Copying the same action twice within one deepcopy must yield the same object
    first, second = deepcopy([action, action])

    assert first is second
