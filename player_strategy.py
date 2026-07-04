"""Simulates Floor 2 fights with user input, allowing you to compare how you stack up against algorithms"""
from copy import deepcopy

from card import Bash, Defend, Strike, Targeting
from character.encounters import fuzzy_wurm_crawler, nibbit, seapunk, shrinker_beetle, sludge_spinner
from collections import defaultdict
from fight import Fight
from character.player import Ironclad
from util.core import Move

CARDS = {
    "strike": Strike(),
    "defend": Defend(),
    "bash": Bash()
}

# Play your way! Displays your hand, draw pile, and discard pile, and reads the next decision from user input.
def user_ironclad(fight: Fight) -> bool:
    player = fight.player
    
    print("Hand:", player.hand)
    print("Draw pile:", player.draw_pile)
    print("Discard pile:", player.discard_pile)

    raw_input = input("To play a card in your hand, enter its name\nTo see the game state, type \"state\"\nTo end your turn, type \"end\"\n")

    print()
    
    if raw_input == "end":
        return True
    elif raw_input == "state":
        print(fight)
        return False
    else:
        if raw_input not in CARDS:
            print("Invalid card", raw_input)
            return False # Prompt again

        card = CARDS[raw_input]

        if player.hand[card] > 0 and card.playable(player.energy):
            player.play(card, target=(None if card.targeting == Targeting.NONE else fight.enemies[0]))
        else:
            print("Card could not be played")
            return False # Prompt again
    


if __name__ == "__main__":
    hp_losses = defaultdict(list)

    for encounter in [fuzzy_wurm_crawler, nibbit, seapunk, shrinker_beetle, sludge_spinner]:
        for _ in range(20):
            player = Ironclad(name="User", player_turn_callback=user_ironclad, verbose=True)
            fight = Fight(player=player, enemies=encounter(verbose=True))
            fight.start()

            print(f"You lost {player.hp} hp")
            hp_losses[encounter].append(player.hp)

    for encounter in [fuzzy_wurm_crawler, nibbit, seapunk, shrinker_beetle, sludge_spinner]:
        print(f"HP losses against {encounter.__name__}: {hp_losses[encounter]}")
        print(f"Average HP loss of against {encounter.__name__}: {sum(hp_losses[encounter]) / len(hp_losses[encounter])}")