import numpy as np

from character.enemies import Nibbit
from character.player import Ironclad
from fight import Fight, MAX_ENEMIES
from util.core import Action
from util.effect import Vulnerable

def test_fight_encodes_to_vector():
    player = Ironclad(name="Test", player_turn_callback=None)
    enemy = Nibbit(name="Test")
    fight = Fight(player=player, enemies=[enemy])

    enemy_vector = enemy.to_vector()
    expected = np.concatenate([
        player.to_vector(),
        enemy_vector,
        np.zeros(len(enemy_vector) * (MAX_ENEMIES - 1), dtype=int),
        [fight.turn],
    ])
    got = fight.to_vector()

    assert np.array_equal(expected, got)

def test_fight_ends_when_enemies_die():
    player = Ironclad(name="Test", player_turn_callback=lambda fight: True)
    enemy1 = Nibbit(name="NibbitOne")
    enemy2 = Nibbit(name="NibbitTwo")
    fight = Fight(player=player, enemies=[enemy1, enemy2])

    enemy1.take_damage(enemy1.hp)
    enemy2.take_damage(enemy2.hp)

    fight.loop()

    assert fight.is_over()

def test_fight_does_not_end_if_player_dies():
    player = Ironclad(name="Test", player_turn_callback=lambda fight: True, hp=100)
    enemy = Nibbit(name="Test")
    fight = Fight(player=player, enemies=[enemy])

    player.take_damage(100)

    fight.loop()

    assert not fight.is_over()

def test_simulate_nibbit_fight():

    def ironclad_premove(fight: Fight) -> bool:
        if fight.turn == 1:
            fight.player.act(fight.enemies[0], Action(damage=6))
            fight.player.act(fight.enemies[0], Action(block=5))
            fight.player.act(fight.enemies[0], Action(block=5))
        elif fight.turn == 2:
            fight.player.act(fight.enemies[0], Action(damage=8, debuffs=[Vulnerable(duration=2)]))
            fight.player.act(fight.enemies[0], Action(block=5))
        elif fight.turn == 3:
            fight.player.act(fight.enemies[0], Action(damage=6))
            fight.player.act(fight.enemies[0], Action(damage=6))
            fight.player.act(fight.enemies[0], Action(damage=6))
        elif fight.turn == 4:
            fight.player.act(fight.enemies[0], Action(damage=8, debuffs=[Vulnerable(duration=2)]))
            fight.player.act(fight.enemies[0], Action(damage=6))
        else: 
            raise AssertionError("Fight should have ended by now")

        return True

    player = Ironclad(name="Test", player_turn_callback=ironclad_premove)
    enemy = Nibbit(name="Test")
    fight = Fight(player=player, enemies=[enemy])

    fight.start()

    assert player.hp == -5
