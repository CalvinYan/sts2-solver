from collections import Counter
from copy import deepcopy
from fractions import Fraction

import numpy as np

from card import AscendersBane, Bash, CardPile, Defend, Strike
from character.enemies import Nibbit, ShrinkerBeetle, SludgeSpinner
from character.enemies.nibbit import HesitantSlice
from character.enemies.shrinker_beetle import Stomp
from character.enemies.sludge_spinner import Slam
from character.player import Ironclad
from fight import MAX_ENEMIES, Fight
from util.core import Action
from util.effect import Shrink, Strength, Vulnerable, Weak


def test_fight_encodes_to_vector():
    player = Ironclad(name="Test", player_turn_callback=None)
    enemy = Nibbit(name="Test")
    fight = Fight(player=player, enemies=[enemy])

    enemy_vector = enemy.to_vector()
    expected = np.concatenate(
        [
            player.to_vector(),
            enemy_vector,
            np.zeros(len(enemy_vector) * (MAX_ENEMIES - 1), dtype=int),
            [fight.turn],
        ]
    )
    got = fight.to_vector()

    assert np.array_equal(expected, got)


def test_fight_decodes_from_vector():
    player = Ironclad(name="Player", player_turn_callback=None)
    enemy = Nibbit(name="Enemy")
    expected = Fight(player=player, enemies=[enemy])

    enemy_vector = enemy.to_vector()
    vector = np.concatenate(
        [
            player.to_vector(),
            enemy_vector,
            np.zeros(len(enemy_vector) * (MAX_ENEMIES - 1), dtype=int),
            [expected.turn],
        ]
    )
    got, read = Fight.from_vector(vector)
    assert expected == got
    assert len(vector) == read


def test_fight_round_trip():
    player = Ironclad(
        name="Player",
        hp=80,
        player_turn_callback=None,
        draw_pile=CardPile(cards=Counter({Defend(): 1})),
        hand=CardPile(cards=Counter({Strike(): 2, Defend(): 1, Bash(): 1, AscendersBane(): 1})),
        discard_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 2})),
        effects=[Weak(duration=2)],
    )
    enemy1 = Nibbit(
        name="Enemy",
        hp=32,
        block=6,
        effects=[Strength(power=3), Vulnerable(duration=2)],
        intent=HesitantSlice(),
    )
    enemy2 = SludgeSpinner(
        name="Enemy",
        hp=19,
        block=0,
        effects=[Strength(power=3)],
        intent=Slam(),
    )
    expected = Fight(player=player, enemies=[enemy1, enemy2], turn=2)
    got, _ = Fight.from_vector(tuple(expected.to_vector()))
    assert expected == got


def test_fight_ends_when_enemies_die():
    player = Ironclad(name="Test", player_turn_callback=lambda fight: True)
    enemy1 = Nibbit(name="NibbitOne")
    enemy2 = Nibbit(name="NibbitTwo")
    fight = Fight(player=player, enemies=[enemy1, enemy2])

    enemy1.take_damage(enemy1.hp)
    enemy2.take_damage(enemy2.hp)

    fight.loop()

    assert fight.is_over()


def test_fight_ends_if_player_dies():
    player = Ironclad(name="Test", player_turn_callback=lambda fight: True, hp=100)
    enemy = Nibbit(name="Test")
    fight = Fight(player=player, enemies=[enemy])

    player.take_damage(100)

    fight.loop()

    assert fight.is_over()


def test_simulate_nibbit_fight():

    def ironclad_premove(fight: Fight) -> bool:
        if fight.turn == 1:
            fight.player.act(fight.enemies[0], Action(damage=6))
            fight.player.act(fight.enemies[0], Action(block=5))
            fight.player.act(fight.enemies[0], Action(block=5))
        elif fight.turn == 2:
            fight.player.act(fight.enemies[0], Action(damage=8, target_effects=[Vulnerable(duration=2)]))
            fight.player.act(fight.enemies[0], Action(block=5))
        elif fight.turn == 3:
            fight.player.act(fight.enemies[0], Action(damage=6))
            fight.player.act(fight.enemies[0], Action(damage=6))
            fight.player.act(fight.enemies[0], Action(damage=6))
        elif fight.turn == 4:
            fight.player.act(fight.enemies[0], Action(damage=8, target_effects=[Vulnerable(duration=2)]))
            fight.player.act(fight.enemies[0], Action(damage=6))
        else:
            raise AssertionError("Fight should have ended by now")

        return True

    player = Ironclad(name="Test", player_turn_callback=ironclad_premove)
    enemy = Nibbit(name="Test")
    fight = Fight(player=player, enemies=[enemy])

    fight.start()

    assert player.hp == 59


def test_search_finds_lethal_against_shrinker_beetle():
    dp_table = dict()
    player = Ironclad(
        name="Player",
        hp=1,
        hand=CardPile(cards=Counter({Strike(): 3, Defend(): 2})),
        effects=[Shrink()],
        player_turn_callback=lambda fight: True,
    )
    enemy = ShrinkerBeetle(name="Enemy", hp=15, intent=Stomp(), effects=[Vulnerable(duration=2)])

    fight = Fight(player=player, enemies=[enemy], turn=1)
    fight_vector = tuple(fight.to_vector())

    hp_losses_expected = {0: Fraction(1, 1)}
    hp_losses_got = fight.search_player_turn(dp_table)
    print(hp_losses_got)
    assert hp_losses_expected == hp_losses_got

    # On this turn, playing a strike guarantees that you have lethal, and playing a defend or passing guarantees you
    # will die
    dp_table_expected = {
        (*fight_vector, Strike().id): {0: Fraction(1, 1)},
        (*fight_vector, Defend().id): {4: Fraction(1, 1)},
        (*fight_vector, -1): {14: Fraction(1, 1)},
    }
    for state_action_pair, hp_losses in dp_table_expected.items():
        assert hp_losses == dp_table[state_action_pair]


def test_search_computes_draw_order_probability():
    dp_table = dict()
    player = Ironclad(
        name="Player",
        hp=1,
        hand=CardPile(cards=Counter({Strike(): 2, Defend(): 3})),
        draw_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 1, Bash(): 1, AscendersBane(): 1})),
        player_turn_callback=lambda fight: True,
    )
    enemy = Nibbit(name="Enemy", hp=18)

    # Nibbit hits for 13 -> Player must triple defend
    # Nibbit hits for 7 -> Player must draw three strikes (50% chance) or they are dead
    fight = Fight(player=player, enemies=[enemy], turn=1)

    hp_losses_expected = {0: Fraction(1, 2), 2: Fraction(1, 2)}
    hp_losses_got = fight.search_player_turn(dp_table)
    assert hp_losses_expected == hp_losses_got


def test_search_uses_cache():
    player = Ironclad(
        name="Player",
        hp=1,
        hand=CardPile(cards=Counter({Strike(): 2, Defend(): 3})),
        draw_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 1, Bash(): 1, AscendersBane(): 1})),
        player_turn_callback=lambda fight: True,
    )
    enemy = Nibbit(name="Enemy", hp=18)
    fight = Fight(player=player, enemies=[enemy], turn=1)

    expected = {
        (*fight.to_vector(), -1): {13: Fraction(1, 1)},
        (*fight.to_vector(), 0): {8: Fraction(1, 1)},
        (*fight.to_vector(), 1): {0: Fraction(1, 2), 2: Fraction(1, 2)},
    }
    got = deepcopy(expected)

    fight.search_player_turn(got)

    # Should not contain additional search states even if a blank-slate search would turn them up
    assert expected == got


def test_search_terminates_at_hp_limit():
    dp_table = dict()
    player = Ironclad(
        name="Player",
        player_turn_callback=lambda fight: True,
    )
    enemy = Nibbit(name="Enemy", hp=20)

    fight = Fight(player=player, enemies=[enemy], turn=1)

    hp_losses = fight.search_player_turn_start(dp_table, hp_limit=57)
    assert all(hp_loss < 7 for hp_loss, _ in hp_losses.items())
