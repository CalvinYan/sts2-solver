"""
A basic demo of the simulator. Provides several naive algorithms for Floor 2 fights and benchmarks them against
different encounters.
"""

import argparse
import cProfile

from copy import deepcopy

from card import Bash, Defend, Strike
from character.encounters import (
    fuzzy_wurm_crawler,
    nibbit,
    seapunk,
    shrinker_beetle,
    sludge_spinner,
)
from collections import defaultdict
from fight import Fight
from character.player import Ironclad
from util.core import Move
from util.effect import Shrink, Vulnerable, Weak


def incoming_damage(fight: Fight) -> int:
    dmg = 0
    for action in fight.enemies[0].intent.actions():
        if action.damage:
            new_action = deepcopy(action)
            move = Move(new_action, actor=fight.enemies[0], target=fight.player)
            for buff in fight.enemies[0].buffs:
                buff.resolve(move, is_target=False)
            for debuff in fight.enemies[0].debuffs:
                debuff.resolve(move, is_target=False)
            for buff in fight.player.buffs:
                buff.resolve(move, is_target=True)
            for debuff in fight.player.debuffs:
                debuff.resolve(move, is_target=True)
            dmg += new_action.damage  # type: ignore

    return dmg


def has_lethal(fight: Fight) -> bool:
    player = fight.player
    enemy = fight.enemies[0]
    max_damage = 0

    shrink_multiplier = 0.7 if Shrink() in player.debuffs else 1
    vuln_multipler = (
        1.5 if any([debuff in enemy.debuffs for debuff in [Vulnerable(duration=1), Vulnerable(duration=2)]]) else 1
    )
    weak_multipler = 0.75 if Weak(duration=1) in player.debuffs else 1

    # Try playing only strikes
    num_strikes = min(player.hand.cards[Strike()], player.energy)
    max_damage = num_strikes * int(6 * shrink_multiplier * vuln_multipler * weak_multipler)

    # Try playing bash first
    if Bash() in player.hand.cards:
        damage = int(8 * shrink_multiplier * vuln_multipler * weak_multipler)
        num_strikes = min(player.hand.cards[Strike()], player.energy - 2)
        damage += num_strikes * int(6 * shrink_multiplier * 1.5 * weak_multipler)
        max_damage = max(max_damage, damage)

    if enemy.block + enemy.hp <= max_damage:
        fight.enemies[0].hp = 0
        return True

    return False


# Attack, attack, attack! Prioritize cards in the following order: Bash, Strike, Defend. Spend all energy.
def unga_bunga_ironclad(fight: Fight) -> bool:
    player = fight.player
    # print("Draw:", player.draw_pile, "Hand:", player.hand, "Discard:", player.discard_pile)
    if has_lethal(fight):
        return True

    bash = Bash()
    strike = Strike()
    defend = Defend()

    if player.hand.cards[bash] > 0 and bash.playable(player.energy):
        player.play(bash, target=fight.enemies[0])

    elif player.hand.cards[strike] > 0 and strike.playable(player.energy):
        player.play(strike, target=fight.enemies[0])

    elif player.hand.cards[defend] > 0 and defend.playable(player.energy):
        player.play(defend, target=None)

    return player.energy == 0 or player.hand.cards.total() == 0  # End turn if no energy left or hand is empty


# The way an inexperienced player might play - block all incoming damage, then priotize Bash, then Strike.
def noob_ironclad(fight: Fight) -> bool:
    player = fight.player
    # print("Draw:", player.draw_pile, "Hand:", player.hand, "Discard:", player.discard_pile)
    if has_lethal(fight):
        return True

    bash = Bash()
    strike = Strike()
    defend = Defend()

    if incoming_damage(fight) > player.block and player.hand.cards[defend] > 0 and defend.playable(player.energy):
        player.play(defend, target=None)

    elif player.hand.cards[bash] > 0 and bash.playable(player.energy):
        player.play(bash, target=fight.enemies[0])

    elif player.hand.cards[strike] > 0 and strike.playable(player.energy):
        player.play(strike, target=fight.enemies[0])

    else:
        return True  # End turn if no cards can be played

    return player.energy == 0 or player.hand.cards.total() == 0  # End turn if no energy left or hand is empty


# A more balanced approach - Play Bash if it's in hand, then block if it would save 5 HP, otherwise play Strike.
def balanced_ironclad(fight: Fight) -> bool:
    player = fight.player
    # print("Draw:", player.draw_pile, "Hand:", player.hand, "Discard:", player.discard_pile)
    if has_lethal(fight):
        return True

    bash = Bash()
    strike = Strike()
    defend = Defend()

    if player.hand.cards[bash] > 0 and bash.playable(player.energy):
        player.play(bash, target=fight.enemies[0])

    elif (
        incoming_damage(fight) >= player.block + 5 and player.hand.cards[defend] > 0 and defend.playable(player.energy)
    ):
        player.play(defend, target=None)

    elif player.hand.cards[strike] > 0 and strike.playable(player.energy):
        player.play(strike, target=fight.enemies[0])

    else:
        return True  # End turn if no cards can be played

    return player.energy == 0 or player.hand.cards.total() == 0  # End turn if no energy left or hand is empty


def main():
    hp_losses = defaultdict(lambda: defaultdict(list))

    for encounter in [
        fuzzy_wurm_crawler,
        nibbit,
        seapunk,
        shrinker_beetle,
        sludge_spinner,
    ]:
        for name, callback in zip(
            ["Chad", "Virgin", "Balanced"],
            [unga_bunga_ironclad, noob_ironclad, balanced_ironclad],
        ):
            for _ in range(10000):
                player = Ironclad(name=name, player_turn_callback=callback)
                starting_hp = player.hp
                fight = Fight(player=player, enemies=encounter())
                fight.start()

                hp_losses[name][encounter].append(starting_hp - player.hp)

    for encounter in [
        fuzzy_wurm_crawler,
        nibbit,
        seapunk,
        shrinker_beetle,
        sludge_spinner,
    ]:
        for name in ["Chad", "Virgin", "Balanced"]:
            print(
                f"Average HP loss of {name} against {encounter.__name__}: {sum(hp_losses[name][encounter]) / len(hp_losses[name][encounter])}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", action="store_true", help="Run main() under cProfile")
    args = parser.parse_args()

    if args.profile:
        cProfile.run("main()", sort="cumulative")
    else:
        main()
