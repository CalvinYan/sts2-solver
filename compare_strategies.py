"""
A basic demo of the simulator. Provides several naive algorithms for Floor 2 fights and benchmarks them against
different encounters.
"""
from copy import deepcopy

from card import Bash, Defend, Strike
from character.encounters import fuzzy_wurm_crawler, nibbit, seapunk, shrinker_beetle, sludge_spinner
from collections import defaultdict
from fight import Fight
from character.player import Ironclad
from util.core import Move

def incoming_damage(fight: Fight) -> int:
    dmg = 0
    for action in fight.enemies[0].intent.actions:
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
            dmg += new_action.damage

    return dmg

def has_lethal(fight: Fight) -> bool:
    # Try playing only strikes
    clone = deepcopy(fight.player)
    clone.name = "Clone1"
    clone.verbose = False
    enemy = deepcopy(fight.enemies[0])
    for _ in range(min(clone.hand.cards[Strike()], clone.energy)):
        clone.play(Strike(), enemy)
        if enemy.hp <= 0:
            fight.enemies[0] = enemy
            return True

    # Try playing bash first
    clone = deepcopy(fight.player)
    clone.name = "Clone2"
    clone.verbose = False
    enemy = deepcopy(fight.enemies[0])
    if Bash() in clone.hand.cards:
        clone.play(Bash(), enemy)
        if enemy.hp <= 0:
            fight.enemies[0] = enemy
            return True
        for _ in range(min(clone.hand.cards[Strike()], clone.energy)):
            clone.play(Strike(), enemy)
            if enemy.hp <= 0:
                fight.enemies[0] = enemy
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

    elif incoming_damage(fight) >= player.block + 5 and player.hand.cards[defend] > 0 and defend.playable(player.energy):
        player.play(defend, target=None)

    elif player.hand.cards[strike] > 0 and strike.playable(player.energy):
        player.play(strike, target=fight.enemies[0])
    
    else:
        return True  # End turn if no cards can be played

    return player.energy == 0 or player.hand.cards.total() == 0  # End turn if no energy left or hand is empty

if __name__ == "__main__":

    hp_losses = defaultdict(lambda: defaultdict(list))

    for encounter in [fuzzy_wurm_crawler, nibbit, seapunk, shrinker_beetle, sludge_spinner]:
        for name, callback in zip(["Chad", "Virgin", "Balanced"], [unga_bunga_ironclad, noob_ironclad, balanced_ironclad]):
            for _ in range(10000):
                player = Ironclad(name=name, player_turn_callback=callback)
                fight = Fight(player=player, enemies=encounter())
                fight.start()

                hp_losses[name][encounter].append(player.hp)

    for encounter in [fuzzy_wurm_crawler, nibbit, seapunk, shrinker_beetle, sludge_spinner]:
        for name in ["Chad", "Virgin", "Balanced"]:
            print(f"Average HP loss of {name} against {encounter.__name__}: {sum(hp_losses[name][encounter]) / len(hp_losses[name][encounter])}")
