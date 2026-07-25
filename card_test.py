from collections import Counter
from fractions import Fraction

import numpy as np
import pytest

from card import AscendersBane, Bash, CardPile, Defend, Strike


def test_card_pile_encodes_to_vector():
    cards = CardPile(cards=Counter({Strike(): 5, Defend(): 4, Bash(): 1, AscendersBane(): 1}))

    expected = np.array([5, 4, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    got = cards.to_vector()

    assert np.array_equal(expected, got)


def test_card_pile_decodes_from_vector():
    vector = np.array([5, 4, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    expected = CardPile(cards=Counter({Strike(): 5, Defend(): 4, Bash(): 1, AscendersBane(): 1}))
    got, read = CardPile.from_vector(vector)
    assert expected == got
    assert len(vector) == read


def test_empty_card_pile_decodes_from_zeroes():
    vector = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    expected = CardPile()
    got, read = CardPile.from_vector(vector)
    assert expected == got
    assert len(vector) == read


def test_card_pile_round_trip():
    expected = CardPile(cards=Counter({Strike(): 1, Defend(): 3, AscendersBane(): 1}))
    got, _ = CardPile.from_vector(tuple(expected.to_vector()))
    assert expected == got


def test_card_pile_overdraws():
    hand = CardPile(cards=Counter({Strike(): 3, Defend(): 2}))
    draw_pile = CardPile(cards=Counter({AscendersBane(): 1}))

    for _ in range(5):
        hand.draw(draw_pile)

    assert hand.cards == Counter({Strike(): 3, Defend(): 2, AscendersBane(): 1})

    assert draw_pile.cards == Counter()


def test_card_pile_draws_distribution():
    deck = CardPile(cards=Counter({Strike(): 5, Defend(): 4, Bash(): 1, AscendersBane(): 1}))

    expected = [
        (CardPile(cards=Counter({Strike(): 5})), Fraction(1, 462)),
        (CardPile(cards=Counter({Strike(): 4, Defend(): 1})), Fraction(20, 462)),
        (CardPile(cards=Counter({Strike(): 4, Bash(): 1})), Fraction(5, 462)),
        (CardPile(cards=Counter({Strike(): 4, AscendersBane(): 1})), Fraction(5, 462)),
        (CardPile(cards=Counter({Strike(): 3, Defend(): 2})), Fraction(60, 462)),
        (CardPile(cards=Counter({Strike(): 3, Defend(): 1, Bash(): 1})), Fraction(40, 462)),
        (CardPile(cards=Counter({Strike(): 3, Defend(): 1, AscendersBane(): 1})), Fraction(40, 462)),
        (CardPile(cards=Counter({Strike(): 3, Bash(): 1, AscendersBane(): 1})), Fraction(10, 462)),
        (CardPile(cards=Counter({Strike(): 2, Defend(): 3})), Fraction(40, 462)),
        (CardPile(cards=Counter({Strike(): 2, Defend(): 2, Bash(): 1})), Fraction(60, 462)),
        (CardPile(cards=Counter({Strike(): 2, Defend(): 2, AscendersBane(): 1})), Fraction(60, 462)),
        (CardPile(cards=Counter({Strike(): 2, Defend(): 1, Bash(): 1, AscendersBane(): 1})), Fraction(40, 462)),
        (CardPile(cards=Counter({Strike(): 1, Defend(): 4})), Fraction(5, 462)),
        (CardPile(cards=Counter({Strike(): 1, Defend(): 3, Bash(): 1})), Fraction(20, 462)),
        (CardPile(cards=Counter({Strike(): 1, Defend(): 3, AscendersBane(): 1})), Fraction(20, 462)),
        (CardPile(cards=Counter({Strike(): 1, Defend(): 2, Bash(): 1, AscendersBane(): 1})), Fraction(30, 462)),
        (CardPile(cards=Counter({Defend(): 4, Bash(): 1})), Fraction(1, 462)),
        (CardPile(cards=Counter({Defend(): 4, AscendersBane(): 1})), Fraction(1, 462)),
        (CardPile(cards=Counter({Defend(): 3, Bash(): 1, AscendersBane(): 1})), Fraction(4, 462)),
    ]

    got = deck.next_hands(5)

    assert len(got) == len(list(expected))

    assert all([draw in got for draw in expected])


def test_card_pile_pops_nothing_from_empty_pile():
    assert CardPile().pop() is None


def test_card_pile_cannot_draw_more_cards_than_it_holds():
    pile = CardPile(cards=Counter({Strike(): 2}))

    with pytest.raises(ValueError):
        pile.next_hands(3)


def test_card_piles_add_and_subtract():
    pile = CardPile(cards=Counter({Strike(): 2, Defend(): 1}))
    other = CardPile(cards=Counter({Strike(): 1}))

    assert (pile + other).cards == Counter({Strike(): 3, Defend(): 1})
    assert (pile - other).cards == Counter({Strike(): 1, Defend(): 1})
    # The operands are left alone
    assert pile.cards == Counter({Strike(): 2, Defend(): 1})
    assert other.cards == Counter({Strike(): 1})


def test_card_pile_arithmetic_rejects_other_types():
    pile = CardPile(cards=Counter({Strike(): 1}))

    with pytest.raises(TypeError):
        pile + Counter({Strike(): 1})

    with pytest.raises(TypeError):
        pile - Counter({Strike(): 1})


def test_card_pile_decodes_from_short_vector():
    with pytest.raises(ValueError):
        CardPile.from_vector((5, 4, 1))


def test_card_pile_str_lists_every_card():
    pile = CardPile(cards=Counter({Strike(): 2, Defend(): 1}))

    assert str(pile) == "[Strike Strike Defend]"
    assert str(CardPile()) == "[]"
