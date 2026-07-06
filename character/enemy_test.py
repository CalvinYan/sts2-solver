import numpy as np

from character.enemies import FuzzyWurmCrawler, Nibbit, SludgeSpinner
from character.enemies.fuzzy_wurm_crawler import AcidGoop1, Inhale, AcidGoop2
from character.enemy import Enemy

def test_enemy_encodes_to_tuple():
    enemy = Nibbit(name="Tibbin")

    expected = (1, enemy.id, enemy.hp, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, enemy.intent.id)
    got = enemy.to_vector()

    assert np.array_equal(expected, got)

def test_enemy_cycles_intents():
    enemy = FuzzyWurmCrawler(name="FWC")

    assert type(enemy.intent) == AcidGoop1

    enemy.resolve_end_of_turn(None)

    assert type(enemy.intent) == Inhale

    enemy.resolve_end_of_turn(None)

    assert type(enemy.intent) == AcidGoop2

    enemy.resolve_end_of_turn(None)

    assert type(enemy.intent) == AcidGoop1

def test_no_enemy_encodes_to_zeroes():
    expected = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    got = Enemy.to_vector(None)

    assert np.array_equal(expected, got)

def test_sludge_spinner_doesnt_repeat_moves():
    enemy = SludgeSpinner(name="Spinner")

    last_intent = None
    # Supppose at any point Sludge Spinner has a .1% chance of repeating a move. Then after 10,000 samples it should
    # repeat at least once with 99.99% certainty
    for _ in range(10000): 
        if type(enemy.intent) == type(last_intent):
            raise AssertionError("Sludge Spinner repeated intent", enemy.intent)

        last_intent = enemy.intent
        enemy.resolve_end_of_turn(None)