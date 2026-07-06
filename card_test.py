import numpy as np

from card import Card, Strike, Defend, Bash, AscendersBane

def test_card_encodes_to_vector():
    card = Strike()

    expected = (1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    got = card.to_vector()

    assert np.array_equal(expected, got)
