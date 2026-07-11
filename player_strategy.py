"""Simulates Floor 2 fights with user input, allowing you to compare how you stack up against algorithms"""

from collections import defaultdict
from fractions import Fraction

from card import Bash, Card, Defend, Strike, Targeting
from character.encounters import ALL_ENCOUNTERS
from character.player import Ironclad
from compare_strategies import has_lethal
from dp_solver import load_dp_table
from fight import Fight

CARDS: dict[str, Card] = {"s": Strike(), "d": Defend(), "b": Bash()}
dp_table: dict[tuple, dict[int, Fraction]] = load_dp_table("./data/dp_data.csv")


# Play your way! Displays your hand, draw pile, and discard pile, and reads the next decision from user input.
def user_ironclad(fight: Fight) -> bool:
    player = fight.player

    print(fight)

    print("Lines:")
    for card in CARDS.values():
        state_action = (*fight.to_vector(), card.id)
        if state_action in dp_table:
            print(card.__class__.__name__, dp_table[state_action])

    if has_lethal(fight):
        print("YOU HAVE LETHAL!")
        return True

    cmds = input(
        'To play a card in your hand, enter its first letter\nTo end your turn, type "e"\nFor example: "b d e"\n'
    ).split()

    print()

    for i, cmd in enumerate(cmds):
        if cmd == "e":
            if i != len(cmds) - 1:
                print(f"The following cards would not be played after ending your turn: {cmds[i+1:]}")
                return False
        else:
            if cmd not in CARDS:
                print(f"Invalid command at position {i}: {cmd}")
                return False  # Prompt again

    for i, cmd in enumerate(cmds):
        if cmd == "e":
            return True

        card = CARDS[cmd]
        if player.hand.cards[card] > 0 and player.can_play(card):
            player.play(
                card,
                target=(None if card.targeting == Targeting.NONE else fight.enemies[0]),
            )
        else:
            print(f"Could not play card {card} at position {i}")
            return False  # Prompt again

    return player.energy == 0


if __name__ == "__main__":
    hp_losses = defaultdict(list)

    for encounter in ALL_ENCOUNTERS:
        for _ in range(20):
            player = Ironclad(name="User", player_turn_callback=user_ironclad, verbose=True)
            starting_hp = player.hp
            fight = Fight(player=player, enemies=encounter(verbose=True))
            fight.start()

            print(f"You lost {starting_hp - player.hp} hp")
            hp_losses[encounter].append(starting_hp - player.hp)

    for encounter in ALL_ENCOUNTERS:
        print(f"HP losses against {encounter.__name__}: {hp_losses[encounter]}")
        print(
            f"Average HP loss of against {encounter.__name__}: {sum(hp_losses[encounter]) / len(hp_losses[encounter])}"
        )
