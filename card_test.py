import numpy as np

from collections import Counter

from card import CardPile, Strike, Defend, Bash, AscendersBane

def test_card_encodes_to_vector():
    card = Strike()

    expected = (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    got = card.to_vector()

    assert np.array_equal(expected, got)

def test_card_pile_encodes_to_vector():
    cards = CardPile(
        cards=Counter({
            Strike(): 5,
            Defend(): 4,
            Bash(): 1,
            AscendersBane(): 1
        })
    )

    expected = np.array([5, 4, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    got = cards.to_vector()

    assert np.array_equal(expected, got)

def test_card_pile_overdraws():
    hand = CardPile(
        cards=Counter({
            Strike(): 3,
            Defend(): 2,
        })
    )
    draw_pile = CardPile(
        cards=Counter({
            AscendersBane(): 1
        })
    )

    for _ in range(5):
        hand.draw(draw_pile)

    assert hand.cards == Counter({
        Strike(): 3,
        Defend(): 2,
        AscendersBane(): 1
    })

    assert draw_pile.cards == Counter()
