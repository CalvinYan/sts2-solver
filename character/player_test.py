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
        energy=3,
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
        1,
        4,
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
        3,
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
        1,
        4,
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
        3,
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
        energy=3,
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
        energy=0,
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
        hand=CardPile(),
        discard_pile=CardPile(cards=Counter({Strike(): 4, Defend(): 4, Bash(): 1})),
    )

    got = clad.next_states()

    for strikes in range(1, 5):
        for bashes in range(min(1, 5 - strikes)):
            defends = 5 - strikes - bashes
            assert (
                CardPile(cards=Counter({Strike(): 5 - strikes, Defend(): 4 - defends, Bash(): 1 - bashes})),
                CardPile(cards=Counter({Strike(): strikes, Defend(): defends, Bash(): bashes})),
                CardPile(),
                Fraction(comb(4, strikes - 1) * comb(4, defends), comb(9, 4)),
            ) in got


def test_player_draws_cards_into_hand():
    clad = Ironclad(
        name="Test",
        player_turn_callback=None,
        draw_pile=CardPile(cards=Counter({Strike(): 5})),
        hand=CardPile(),
    )

    clad.draw(3)

    # A pile of identical cards makes the result independent of draw order
    assert clad.hand.cards == Counter({Strike(): 3})
    assert clad.draw_pile.cards == Counter({Strike(): 2})


def test_player_draw_reshuffles_discard_when_draw_pile_empty():
    clad = Ironclad(
        name="Test",
        player_turn_callback=None,
        draw_pile=CardPile(),
        hand=CardPile(),
        discard_pile=CardPile(cards=Counter({Defend(): 4})),
    )

    clad.draw(2)

    assert clad.hand.cards == Counter({Defend(): 2})
    assert clad.draw_pile.cards == Counter({Defend(): 2})
    assert clad.discard_pile.cards == Counter()


def test_player_draw_stops_when_hand_full():
    clad = Ironclad(
        name="Test",
        player_turn_callback=None,
        draw_pile=CardPile(cards=Counter({Strike(): 3})),
        hand=CardPile(cards=Counter({Defend(): 10})),
    )

    clad.draw(1)

    # Hand is already at the 10-card cap, so nothing is drawn
    assert clad.hand.cards == Counter({Defend(): 10})
    assert clad.draw_pile.cards == Counter({Strike(): 3})


def test_player_resolve_start_of_turn():
    clad = Ironclad(
        name="Test",
        block=5,
        energy=0,
        player_turn_callback=None,
        draw_pile=CardPile(cards=Counter({Strike(): 10})),
        hand=CardPile(),
    )

    clad.resolve_start_of_turn()

    assert clad.block == 0
    assert clad.energy == 3
    assert clad.hand.cards == Counter({Strike(): 5})
    assert clad.draw_pile.cards == Counter({Strike(): 5})


def test_player_resolve_end_of_turn_exhausts_ascenders_bane_and_discards_hand():
    clad = Ironclad(
        name="Test",
        player_turn_callback=None,
        draw_pile=CardPile(),
        hand=CardPile(cards=Counter({Strike(): 2, AscendersBane(): 1})),
        discard_pile=CardPile(cards=Counter({Defend(): 1})),
        effects=[Weak(duration=2)],
    )

    clad.resolve_end_of_turn()

    # Ascender's Bane is exhausted rather than discarded; the rest of the hand moves to the discard pile
    assert clad.hand.cards == Counter()
    assert clad.discard_pile.cards == Counter({Strike(): 2, Defend(): 1})
    # Effect durations still tick down at end of turn
    assert clad.effects == [Weak(duration=1)]
