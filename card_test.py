import numpy as np

from collections import Counter
from fractions import Fraction

from card import CardPile, Strike, Defend, Bash, AscendersBane


def test_card_encodes_to_vector():
    card = Strike()

    expected = (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    got = card.to_vector()

    assert np.array_equal(expected, got)


def test_card_pile_encodes_to_vector():
    cards = CardPile(cards=Counter({Strike(): 5, Defend(): 4, Bash(): 1, AscendersBane(): 1}))

    expected = np.array([5, 4, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    got = cards.to_vector()

    assert np.array_equal(expected, got)


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
