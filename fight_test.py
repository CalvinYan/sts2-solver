from collections import Counter

import numpy as np

from card import AscendersBane, Bash, CardPile, Defend, Strike
from character.enemies import Nibbit, SludgeSpinner
from character.enemies.nibbit import HesitantSlice
from character.enemies.sludge_spinner import Slam
from character.player import Ironclad
from fight import MAX_ENEMIES, Fight
from util.core import Action
from util.effect import Strength, Vulnerable, Weak


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
