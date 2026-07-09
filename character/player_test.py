from collections import Counter
from fractions import Fraction
from math import comb

import numpy as np

from card import AscendersBane, Bash, CardPile, Defend, Strike
from character.player import Ironclad, Player
from util.effect import Strength, Thorns, Weak


def test_player_encodes_to_vector():
    clad = Ironclad(
        name="Test",
        hp=80,
        player_turn_callback=None,
        draw_pile=CardPile(cards=Counter({Defend(): 1})),
        hand=CardPile(cards=Counter({Strike(): 2, Defend(): 1, Bash(): 1, AscendersBane(): 1})),
        discard_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 2})),
        effects=[Strength(power=4), Weak(duration=2)],
    )

    expected = (
        0,
        80,
        0,
        4,
        0,
        0,
        0,
        0,
        0,
        0,
        2,
        0,
        0,
        0,
        0,
        0,
        1,
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
        2,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        3,
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
    )
    got = clad.to_vector()
    assert np.array_equal(expected, got)


def test_player_decodes_from_vector():
    vector = (
        0,
        80,
        0,
        4,
        0,
        0,
        0,
        0,
        0,
        0,
        2,
        0,
        0,
        0,
        0,
        0,
        1,
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
        2,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        3,
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
    )
    expected = Ironclad(
        name="Player",
        hp=80,
        player_turn_callback=None,
        draw_pile=CardPile(cards=Counter({Defend(): 1})),
        hand=CardPile(cards=Counter({Strike(): 2, Defend(): 1, Bash(): 1, AscendersBane(): 1})),
        discard_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 2})),
        effects=[Strength(power=4), Weak(duration=2)],
    )
    got, read = Player.from_vector(vector)
    assert expected == got
    assert len(vector) == read


def test_player_round_trip():
    expected = Ironclad(
        name="Player",
        hp=64,
        player_turn_callback=None,
        draw_pile=CardPile(cards=Counter({Strike(): 2, Defend(): 3, Bash(): 1})),
        hand=CardPile(cards=Counter({Strike(): 1, AscendersBane(): 1})),
        discard_pile=CardPile(cards=Counter({Strike(): 2, Defend(): 1})),
        effects=[Thorns(power=3)],
    )
    got, _ = Player.from_vector(tuple(expected.to_vector()))
    assert expected == got


def test_player_next_states_reshuffle():
    clad = Ironclad(
        name="Test",
        player_turn_callback=None,
        draw_pile=CardPile(cards=Counter({Strike(): 1})),
        hand=CardPile(
            cards=Counter(
                {
                    Strike(): 1,
                    Defend(): 3,
                    Bash(): 1,
                }
            )
        ),
        discard_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 1})),
    )

    got = clad.next_states()

    for strikes in range(1, 5):
        for bashes in range(min(1, 5 - strikes)):
            defends = 5 - strikes - bashes
            assert (
                Ironclad(
                    name="Test",
                    player_turn_callback=None,
                    draw_pile=CardPile(
                        cards=Counter(
                            {
                                Strike(): 5 - strikes,
                                Defend(): 4 - defends,
                                Bash(): 1 - bashes,
                            }
                        )
                    ),
                    hand=CardPile(cards=Counter({Strike(): strikes, Defend(): defends, Bash(): bashes})),
                ),
                Fraction(comb(4, strikes - 1) * comb(4, defends), comb(9, 4)),
            ) in got
