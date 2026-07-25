from collections import Counter
from copy import deepcopy
from fractions import Fraction
from unittest.mock import patch

import numpy as np

from card import AscendersBane, Bash, CardPile, Defend, FallingStar, Strike, Venerate
from character.enemies import (
    FuzzyWurmCrawler,
    Nibbit,
    ShrinkerBeetle,
    SludgeSpinner,
    Toadpole,
)
from character.enemies.nibbit import Butt, HesitantSlice, Hiss
from character.enemies.shrinker_beetle import Stomp
from character.enemies.sludge_spinner import Rage, Slam
from character.enemies.toadpole import Spiken, SpikeSpit, Whirl
from character.enemy import Enemy
from character.player import Ironclad, Regent
from fight import MAX_ENEMIES, Fight
from search.table import QTable
from util.core import Action
from util.effect import Shrink, Strength, Vulnerable, Weak


def test_fight_encodes_to_vector():
    player = Ironclad()
    enemy = Nibbit()
    fight = Fight(player=player, enemies=[enemy])

    enemy_vector = enemy.to_vector()
    expected = np.concatenate(
        [
            player.to_vector(),
            enemy_vector,
            *[Enemy.to_vector(None) for _ in range(MAX_ENEMIES - 1)],
        ]
    )
    got = fight.to_vector()

    assert np.array_equal(expected, got)


def test_full_fight_encodes_to_vector():
    player = Ironclad()
    enemies = [Nibbit(hp=40 + i) for i in range(MAX_ENEMIES)]
    fight = Fight(player=player, enemies=enemies)

    # A fight with every enemy slot occupied needs no padding
    expected = np.concatenate([player.to_vector(), *[enemy.to_vector() for enemy in enemies]])
    got = fight.to_vector()

    assert np.array_equal(expected, got)


def test_fight_decodes_from_vector():
    player = Ironclad()
    enemy = Nibbit()
    expected = Fight(player=player, enemies=[enemy])

    enemy_vector = enemy.to_vector()
    vector = [
        *player.to_vector(),
        *enemy_vector,
        *(0 for _ in range(len(enemy_vector) * (MAX_ENEMIES - 1))),
    ]
    got, read = Fight.from_vector(vector)
    assert expected == got
    assert len(vector) == read


def test_fight_round_trip():
    player = Ironclad(
        hp=80,
        draw_pile=CardPile(cards=Counter({Defend(): 1})),
        hand=CardPile(cards=Counter({Strike(): 2, Defend(): 1, Bash(): 1, AscendersBane(): 1})),
        discard_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 2})),
        effects=[Weak(duration=2)],
    )
    enemy1 = Nibbit(
        hp=32,
        block=6,
        effects=[Strength(power=3), Vulnerable(duration=2)],
        intent=HesitantSlice(),
    )
    enemy2 = SludgeSpinner(
        hp=19,
        block=0,
        effects=[Strength(power=3)],
        intent=Slam(),
    )
    expected = Fight(player=player, enemies=[enemy1, enemy2])
    got, _ = Fight.from_vector(tuple(expected.to_vector()))
    assert expected == got


def test_fight_ends_when_enemies_die():
    player = Ironclad()
    enemy1 = Nibbit(name="NibbitOne")
    enemy2 = Nibbit(name="NibbitTwo")
    fight = Fight(player=player, enemies=[enemy1, enemy2])

    enemy1.take_damage(enemy1.hp)
    enemy2.take_damage(enemy2.hp)

    fight.loop()

    assert fight.is_over()


def test_fight_ends_if_player_dies():
    player = Ironclad()
    enemy = Nibbit()
    fight = Fight(player=player, enemies=[enemy])

    player.take_damage(100)

    fight.loop()

    assert fight.is_over()


def test_fight_incoming_damage_sums_every_attack():
    # HesitantSlice deals 7 damage and gains 6 block; only the damage counts
    slicer = Nibbit(hp=30, intent=HesitantSlice())
    # SpikeSpit deals 4 damage three times, plus one action that deals no damage
    spitter = Toadpole(hp=20, intent=SpikeSpit())
    fight = Fight(player=Ironclad(), enemies=[slicer, spitter])

    assert fight.incoming_damage() == 7 + 4 * 3


def test_fight_incoming_damage_applies_effects_of_both_sides():
    enemy = Nibbit(hp=30, intent=Butt(), effects=[Strength(power=3)])  # Butt deals 13 damage
    player = Ironclad(effects=[Vulnerable(duration=1)])
    fight = Fight(player=player, enemies=[enemy])

    assert fight.incoming_damage() == int((13 + 3) * 1.5)


def test_fight_incoming_damage_does_not_mutate_the_fight():
    enemy = Nibbit(hp=30, intent=Butt(), effects=[Strength(power=3)])
    player = Ironclad(effects=[Vulnerable(duration=1)])
    fight = Fight(player=player, enemies=[enemy])
    expected = fight.to_vector()

    # Repeated queries must agree with each other and leave the fight untouched
    assert fight.incoming_damage() == fight.incoming_damage()
    assert expected == fight.to_vector()


def test_fight_incoming_damage_ignores_non_attacking_intents():
    fight = Fight(player=Ironclad(), enemies=[Nibbit(hp=30, intent=Hiss())])

    assert fight.incoming_damage() == 0


def test_simulate_nibbit_fight():
    class Testclad(Ironclad):
        def resolve_turn(self, fight: Fight) -> bool:
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

    player = Testclad()
    enemy = Nibbit()
    fight = Fight(player=player, enemies=[enemy])

    fight.start()

    assert player.hp == 59


def test_search_no_mutate_fight():
    player = Ironclad()
    enemy = FuzzyWurmCrawler(hp=58)
    fight = Fight(player=player, enemies=[enemy])
    expected = fight.to_vector()
    fight.search_player_turn_start(QTable(), QTable(), hp_limit=58)

    assert expected == fight.to_vector()


def test_search_truncates_after_finding_lethal():
    dp_table = QTable()
    fully_explored = QTable()
    player = Ironclad(
        hp=1,
        hand=CardPile(cards=Counter({Strike(): 3, Defend(): 2})),
        effects=[Shrink()],
    )
    enemy = ShrinkerBeetle(hp=15, intent=Stomp(), effects=[Vulnerable(duration=2)])

    fight = Fight(player=player, enemies=[enemy], turn=1)
    fight_vector = tuple(fight.to_vector())

    hp_losses_expected = {0: Fraction(1)}
    hp_losses_got, search_complete = fight.search_player_turn(dp_table, fully_explored)
    assert hp_losses_expected == hp_losses_got
    assert search_complete

    # Search should terminate once it finds that triple Strike is lethal
    dp_table_expected = QTable({(fight_vector, (Strike().id, 0)): {0: Fraction(1)}})
    for state_action_pair, hp_losses in dp_table_expected.items():
        assert hp_losses == dp_table[state_action_pair]


def test_search_fully_computes_unwinnable_turn():
    dp_table = QTable()
    fully_explored = QTable()
    player = Ironclad(
        hp=1,
        hand=CardPile(cards=Counter({Strike(): 3, Defend(): 2})),
        effects=[Shrink()],
    )
    enemy = ShrinkerBeetle(hp=20, intent=Stomp(), effects=[Vulnerable(duration=2)])

    # Precalculate the expected DP table
    fight = Fight(player=player, enemies=[enemy], turn=2)
    dp_table_expected = QTable()

    for strikes in range(4):
        for defends in range(min(2, 3 - strikes) + 1):
            fight_copy = deepcopy(fight)
            for _ in range(strikes):
                fight_copy.player.play(Strike(), fight_copy.enemies[0])
            for _ in range(defends):
                fight_copy.player.play(Defend())

            if strikes + defends == 3:
                dp_table_expected[(fight_copy.to_vector(), (-1,))] = {14 - 5 * defends: Fraction(1)}
            if strikes < 3 and strikes + defends < 3:
                dp_table_expected[(fight_copy.to_vector(), (Strike().id, 0))] = {
                    14 - 5 * min(2, 2 - strikes): Fraction(1)
                }
            if defends < 2 and strikes + defends < 3:
                dp_table_expected[(fight_copy.to_vector(), (Defend().id,))] = {9 - 5 * min(1, 2 - strikes): Fraction(1)}

    hp_losses_expected = {4: Fraction(1)}
    hp_losses_got, search_complete = fight.search_player_turn(dp_table, fully_explored)
    assert hp_losses_expected == hp_losses_got
    assert search_complete

    # Player is dead no matter what, but search should tabulate all the possible ways
    assert dp_table_expected == dp_table


def test_search_computes_draw_order_probability():
    dp_table = QTable()
    fully_explored = QTable()
    player = Ironclad(
        hp=1,
        hand=CardPile(cards=Counter({Strike(): 2, Defend(): 3})),
        draw_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 1, Bash(): 1, AscendersBane(): 1})),
    )
    enemy = Nibbit(hp=18)

    # Nibbit hits for 13 -> Player must triple defend
    # Nibbit hits for 7 -> Player must draw three strikes (50% chance) or they are dead
    fight = Fight(player=player, enemies=[enemy], turn=1)

    hp_losses_expected = {0: Fraction(1, 2), 2: Fraction(1, 2)}
    hp_losses_got, search_complete = fight.search_player_turn(dp_table, fully_explored)
    assert hp_losses_expected == hp_losses_got
    assert search_complete


def test_search_uses_cache():
    player = Ironclad(
        hp=1,
        hand=CardPile(cards=Counter({Strike(): 2, Defend(): 3})),
        draw_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 1, Bash(): 1, AscendersBane(): 1})),
    )
    enemy = Nibbit(hp=18)
    fight = Fight(player=player, enemies=[enemy], turn=1)

    expected = {
        (fight.to_vector(), (-1,)): {13: Fraction(1)},
        (fight.to_vector(), (Strike().id, 0)): {8: Fraction(1)},
        (fight.to_vector(), (Defend().id,)): {0: Fraction(1, 2), 2: Fraction(1, 2)},
    }
    got = deepcopy(expected)
    fully_explored = deepcopy(expected)

    fight.search_player_turn(got, fully_explored)

    # Should not contain additional search states even if a blank-slate search would turn them up
    assert expected == got


def test_search_terminates_at_hp_limit():
    dp_table = QTable()
    fully_explored = QTable()
    player = Ironclad()
    enemy = Nibbit(hp=20)

    fight = Fight(player=player, enemies=[enemy], turn=1)

    _, search_complete = fight.search_player_turn_start(dp_table, fully_explored, hp_limit=57)
    assert not search_complete


def test_search_no_cache_incomplete_results():
    player = Ironclad(
        hp=50,
        energy=1,
        hand=CardPile(cards=Counter({Strike(): 1, Defend(): 1})),
        draw_pile=CardPile(cards=Counter({Strike(): 4, Defend(): 1})),
    )
    enemy = FuzzyWurmCrawler(hp=12)
    fight = Fight(player=player, enemies=[enemy], turn=1)
    vector = fight.to_vector()

    dp_table = QTable()
    fully_explored = QTable()

    fight.search_player_turn(dp_table, fully_explored, hp_limit=48)

    assert (vector, (Strike().id, 0)) in dp_table
    assert (vector, (Defend().id,)) in dp_table

    assert (vector, (Strike().id, 0)) not in fully_explored
    assert (vector, (Defend().id,)) in fully_explored


def test_search_no_defend_on_empty_turn():
    dp_table = QTable()
    fully_explored = QTable()
    player = Ironclad(
        hand=CardPile(cards=Counter({Bash(): 1, Strike(): 1, AscendersBane(): 1, Defend(): 2})),
        draw_pile=CardPile(cards=Counter({Strike(): 4, Defend(): 2})),
    )
    enemy = Nibbit(hp=15, intent=Hiss())

    fight = Fight(player=player, enemies=[enemy], turn=3)

    fight.search_player_turn(dp_table, fully_explored)
    # Search should not ever consider playing Defend
    assert not any(vector[-1] == Defend.id for vector in dp_table.keys())


def test_search_no_overblock():
    dp_table = QTable()
    fully_explored = QTable()
    player = Ironclad(
        block=10,
        energy=1,
        hand=CardPile(cards=Counter({Bash(): 1, Strike(): 1, Defend(): 1})),
        draw_pile=CardPile(cards=Counter({Strike(): 4, Defend(): 1})),
    )
    enemy = Nibbit(hp=12, intent=HesitantSlice())

    fight = Fight(player=player, enemies=[enemy], turn=2)

    fight.search_player_turn(dp_table, fully_explored)
    # Search should not ever consider playing Defend
    assert not any(vector[-1] == Defend.id for vector in dp_table.keys())


def test_search_no_premature_end_turn():
    player = Ironclad(
        hand=CardPile(cards=Counter({Strike(): 1, Defend(): 1})),
        draw_pile=CardPile(cards=Counter({Strike(): 4, Defend(): 1})),
    )
    enemy = FuzzyWurmCrawler(hp=12)
    fight = Fight(player=player, enemies=[enemy], turn=1)
    vector = fight.to_vector()

    dp_table = QTable()
    fully_explored = QTable()

    fight.search_player_turn(dp_table, fully_explored, hp_limit=48)

    assert (vector, (-1,)) not in dp_table
    assert (vector, (-1,)) not in fully_explored


def test_single_enemy_all_intents_searched():
    next_intents = set()

    def search_player_turn_start(
        self,
        dp_table: QTable,
        fully_explored: QTable,
        hp_limit: int = 0,
    ) -> tuple[dict[int, Fraction], bool]:
        next_intents.add(self.enemies[0].intent)
        return ({0: Fraction(1)}, True)

    dp_table = QTable()
    fully_explored = QTable()
    player = Ironclad(draw_pile=CardPile(cards=Counter({Strike(): 4, Bash(): 1})))
    enemy = SludgeSpinner()
    fight = Fight(player=player, enemies=[enemy], turn=1)
    with patch.object(Fight, "search_player_turn_start", search_player_turn_start):
        fight.search_enemy_turn_end(dp_table, fully_explored)

    assert next_intents == {Slam(), Rage()}


def test_multiple_enemies_all_intents_searched():
    intent_combos = set()

    def search_player_turn_start(
        self,
        dp_table: QTable,
        fully_explored: QTable,
        hp_limit: int = 0,
    ) -> tuple[dict[int, Fraction], bool]:
        intent_combos.add(tuple(enemy.intent for enemy in self.enemies))
        return ({0: Fraction(1)}, True)

    dp_table = QTable()
    fully_explored = QTable()
    player = Ironclad(
        hp=1,
        hand=CardPile(),
        draw_pile=CardPile(cards=Counter({Strike(): 4, Bash(): 1})),
    )
    tweedle_dee = SludgeSpinner(name="Tweedle Dee")
    tweedle_dum = SludgeSpinner(name="Tweedle Dum")
    fight = Fight(player=player, enemies=[tweedle_dee, tweedle_dum], turn=1)
    with patch.object(Fight, "search_player_turn_start", search_player_turn_start):
        fight.search_enemy_turn_end(dp_table, fully_explored)

    assert intent_combos == {(Slam(), Slam()), (Slam(), Rage()), (Rage(), Slam()), (Rage(), Rage())}


def test_search_multiple_enemies_lethal_found():
    dp_table = QTable()
    fully_explored = QTable()

    toadpole_one = Toadpole(name="Toadpole One", hp=6, intent=Spiken())
    toadpole_two = Toadpole(name="Toadpole Two", hp=17, intent=Whirl())

    player = Regent(hp=1, stars=1, hand=CardPile(Counter({Strike(): 2, Defend(): 1, FallingStar(): 1, Venerate(): 1})))

    fight = Fight(player=player, enemies=[toadpole_one, toadpole_two], turn=1)
    state_vector = fight.to_vector()
    hp_losses, search_complete = fight.search_player_turn(dp_table, fully_explored)

    assert search_complete
    assert hp_losses == {0: Fraction(1)}
    assert (state_vector, (Strike().id, 0)) in fully_explored
    assert fully_explored[(state_vector, (Strike().id, 0))] == {0: Fraction(1)}


def test_search_multiple_enemies_clear_dead_enemies():
    dp_table = QTable()
    fully_explored = QTable()

    toadpole_one = Toadpole(name="Toadpole One", hp=5, intent=Spiken())
    toadpole_two = Toadpole(name="Toadpole Two", hp=7, intent=Whirl())

    player = Ironclad()

    fight = Fight(player=player, enemies=[toadpole_one, toadpole_two])
    fight.search_player_turn_start(dp_table, fully_explored)

    for state_vector, _ in fully_explored.keys():
        state, _ = Fight.from_vector(state_vector)
        assert not any([enemy.hp <= 0 for enemy in state.enemies])


def test_search_computes_regent_turn():
    dp_table = QTable()
    fully_explored = QTable()
    player = Regent(
        hp=1,
        stars=0,
        draw_pile=CardPile(cards=Counter({Strike(): 3, Defend(): 2, AscendersBane(): 1})),
        hand=CardPile(cards=Counter({Strike(): 1, Defend(): 2, Venerate(): 1, FallingStar(): 1})),
    )
    enemy = Nibbit(hp=20)

    fight = Fight(player=player, enemies=[enemy], turn=1)

    # Turn 1: Venerate -> FallingStar -> Defend x2
    # Turn 2: Guaranteed lethal
    hp_losses_expected = {0: Fraction(1)}
    hp_losses_got, search_complete = fight.search_player_turn(dp_table, fully_explored)
    assert hp_losses_expected == hp_losses_got
    assert search_complete


def test_long_search_with_hp_limit():
    dp_table = QTable()
    fully_explored = QTable()
    player = Ironclad()
    enemy = FuzzyWurmCrawler(hp=58)
    fight = Fight(player=player, enemies=[enemy])

    hp_losses_expected = {
        4: Fraction(9617, 116424),
        6: Fraction(2377, 3234),
        8: Fraction(141, 1078),
        9: Fraction(4751, 145530),
        11: Fraction(5, 2156),
        13: Fraction(83, 6468),
        14: Fraction(67, 17640),
    }
    hp_losses_got, search_complete = fight.search_player_turn_start(dp_table, fully_explored, hp_limit=59)

    assert hp_losses_expected == hp_losses_got
    assert not search_complete
