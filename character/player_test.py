from collections import Counter
from fractions import Fraction
from math import comb

from card import Bash, CardPile, Defend, Strike
from character.player import Ironclad


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
